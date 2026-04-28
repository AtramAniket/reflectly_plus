from sqlalchemy.exc import SQLAlchemyError
from flask_login import login_required, current_user
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from app.extensions import db
from app.models.mood_checklist import MoodChecklistResult
from app.models.procrastination_sheet import ProcrastinationSheet, ProcrastinationTask
from app.helper.procrastination_sheets_helper import get_sheet_stats, MAX_PROCRASTINATION_TASKS
from app.forms.procrastination_forms import ProcrastinationSheetForm, ProcrastinationTaskForm,CompleteProcrastinationTaskForm
from app.helper.mood_wellbeing_check import (
    CHECKLIST_QUESTIONS,
    get_checklist_feedback,
    get_checklist_question_texts,
    build_grouped_checklist_sections,
)

tools = Blueprint('tools', __name__)

@tools.route("/tools/mood-checklist", methods=["GET", "POST"])
@login_required
def mood_checklist():
    if request.method == "POST":
        try:
            answers = {}

            for idx in range(len(CHECKLIST_QUESTIONS)):
                raw_value = request.form.get(f"q_{idx}")

                if raw_value is None or raw_value == "":
                    flash("Please answer every question before submitting.", "error")
                    return redirect(request.url)

                value = int(raw_value)

                if value < 0 or value > 4:
                    flash("Each response must be between 0 and 4.", "error")
                    return redirect(request.url)

                answers[f"q_{idx}"] = value

            note = request.form.get("note", "").strip() or None
            total_score = sum(answers.values())

            result = MoodChecklistResult(
                user_id=current_user.id,
                answers=answers,
                total_score=total_score,
                note=note
            )

            db.session.add(result)
            db.session.commit()

            flash("Check-in submitted successfully.", "success")
            return redirect(url_for("tools.view_mood_checklist_result", result_id=result.id))

        except ValueError:
            db.session.rollback()
            flash("One or more responses were invalid.", "error")
            return redirect(request.url)

        except SQLAlchemyError:
            db.session.rollback()
            flash("Something went wrong while saving your check-in.", "error")
            return redirect(request.url)

    return render_template(
        "tools/mood_checklist.html",
        questions=get_checklist_question_texts()
    )


@tools.route("/tools/mood-checklist/history")
@login_required
def mood_checklist_history():
    results = (
        MoodChecklistResult.query
        .filter_by(user_id=current_user.id)
        .order_by(MoodChecklistResult.created_at.desc())
        .all()
    )

    return render_template(
        "tools/mood_checklist_history.html",
        results=results,
        get_checklist_feedback=get_checklist_feedback
    )


@tools.route("/tools/mood-checklist/<int:result_id>")
@login_required
def view_mood_checklist_result(result_id):
    result = MoodChecklistResult.query.get_or_404(result_id)

    if result.user_id != current_user.id:
        abort(403)

    feedback = get_checklist_feedback(result.total_score)
    grouped_response_sections = build_grouped_checklist_sections(result.answers)

    return render_template(
        "tools/view_mood_checklist_result.html",
        result=result,
        feedback=feedback,
        grouped_response_sections=grouped_response_sections
    )

# /tools/anti-procratination

@tools.route("/tools/anti-procrastination", methods=["GET", "POST"])
@login_required
def anti_procrastination():
    form = ProcrastinationSheetForm()

    if form.validate_on_submit():
        try:
            sheet = ProcrastinationSheet(
                user_id=current_user.id,
                title=form.title.data.strip(),
                note=form.note.data.strip() or None
            )

            db.session.add(sheet)
            db.session.commit()

            flash("New worksheet created. Add your first task when you're ready.", "success")
            return redirect(url_for("tools.view_procrastination_sheet", sheet_id=sheet.id))

        except SQLAlchemyError:
            db.session.rollback()
            flash("Something went wrong while creating your worksheet.", "error")
            return redirect(request.url)

    return render_template(
        "tools/anti_procrastination.html",
        form=form
    )


@tools.route("/tools/anti-procrastination/<int:sheet_id>")
@login_required
def view_procrastination_sheet(sheet_id):
    sheet = ProcrastinationSheet.query.get_or_404(sheet_id)

    if sheet.user_id != current_user.id:
        abort(403)

    stats = get_sheet_stats(sheet)

    return render_template(
        "tools/view_procrastination_sheet.html",
        sheet=sheet,
        stats=stats,
        max_tasks=MAX_PROCRASTINATION_TASKS
    )


@tools.route("/tools/anti-procrastination/<int:sheet_id>/add-task", methods=["GET", "POST"])
@login_required
def add_procrastination_task(sheet_id):
    sheet = ProcrastinationSheet.query.get_or_404(sheet_id)

    if sheet.user_id != current_user.id:
        abort(403)

    if len(sheet.tasks) >= MAX_PROCRASTINATION_TASKS:
        flash("This worksheet already has the maximum number of tasks.", "warning")
        return redirect(url_for("tools.view_procrastination_sheet", sheet_id=sheet.id))

    form = ProcrastinationTaskForm()

    if form.validate_on_submit():
        try:
            task = ProcrastinationTask(
                sheet_id=sheet.id,
                task_name=form.task_name.data.strip(),
                avoidance_reason=form.avoidance_reason.data.strip() or None,
                resistance_thoughts=form.resistance_thoughts.data.strip() or None,
                tiny_step=form.tiny_step.data.strip(),
                expected_difficulty=form.expected_difficulty.data,
                expected_satisfaction=form.expected_satisfaction.data
            )

            db.session.add(task)
            db.session.commit()

            flash("Task added to worksheet.", "success")
            return redirect(url_for("tools.view_procrastination_sheet", sheet_id=sheet.id))

        except SQLAlchemyError:
            db.session.rollback()
            flash("Something went wrong while adding your task.", "error")
            return redirect(request.url)

    return render_template(
        "tools/add_procrastination_task.html",
        sheet=sheet,
        form=form,
        max_tasks=MAX_PROCRASTINATION_TASKS
    )


@tools.route("/tools/anti-procrastination/task/<int:task_id>/complete", methods=["GET", "POST"])
@login_required
def complete_procrastination_task(task_id):
    task = ProcrastinationTask.query.get_or_404(task_id)
    sheet = task.sheet

    if sheet.user_id != current_user.id:
        abort(403)

    form = CompleteProcrastinationTaskForm(obj=task)

    if form.validate_on_submit():
        try:
            task.actual_difficulty = form.actual_difficulty.data
            task.actual_satisfaction = form.actual_satisfaction.data
            task.reflection = form.reflection.data.strip() or None
            task.is_completed = True

            db.session.commit()

            flash("Task review saved.", "success")
            return redirect(url_for("tools.view_procrastination_sheet", sheet_id=sheet.id))

        except SQLAlchemyError:
            db.session.rollback()
            flash("Something went wrong while saving this task review.", "error")
            return redirect(request.url)

    return render_template(
        "tools/complete_procrastination_task.html",
        task=task,
        sheet=sheet,
        form=form
    )


@tools.route("/tools/anti-procrastination/history")
@login_required
def procrastination_sheet_history():
    sheets = (
        ProcrastinationSheet.query
        .filter_by(user_id=current_user.id)
        .order_by(ProcrastinationSheet.created_at.desc())
        .all()
    )

    return render_template(
        "tools/procrastination_sheet_history.html",
        sheets=sheets,
        get_sheet_stats=get_sheet_stats,
        max_tasks=MAX_PROCRASTINATION_TASKS
    )