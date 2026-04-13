from sqlalchemy.exc import SQLAlchemyError
from flask_login import login_required, current_user
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from app.extensions import db
from app.models.mood_checklist import MoodChecklistResult
from app.helper.procrastination_sheets_helper import get_sheet_stats
from app.models.procrastination_sheet import ProcrastinationSheet, ProcrastinationTask
from app.helper.mood_wellbeing_check import CHECKLIST_QUESTIONS, get_checklist_feedback

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
        questions=CHECKLIST_QUESTIONS
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

    question_answer_pairs = [
        {
            "question": question,
            "score": result.answers.get(f"q_{idx}", 0)
        }
        for idx, question in enumerate(CHECKLIST_QUESTIONS)
    ]

    return render_template(
        "tools/view_mood_checklist_result.html",
        result=result,
        feedback=feedback,
        question_answer_pairs=question_answer_pairs
    )

# /tools/anti-procratination

@tools.route("/tools/anti-procrastination", methods=["GET", "POST"])
@login_required
def anti_procrastination():
    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()
            note = request.form.get("note", "").strip() or None

            if not title:
                flash("Sheet title is required.", "error")
                return redirect(request.url)

            sheet = ProcrastinationSheet(
                user_id=current_user.id,
                title=title,
                note=note
            )

            db.session.add(sheet)
            db.session.commit()

            flash("New anti-procrastination sheet created.", "success")
            return redirect(url_for("tools.view_procrastination_sheet", sheet_id=sheet.id))

        except SQLAlchemyError:
            db.session.rollback()
            flash("Something went wrong while creating your sheet.", "error")
            return redirect(request.url)

        except Exception as e:
            db.session.rollback()
            print("CREATE SHEET ERROR:", e)
            flash("Unexpected error occurred. Please try again.", "error")
            return redirect(request.url)

    return render_template("tools/anti_procrastination.html")


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
        flash("This sheet already has the maximum number of tasks.", "warning")
        return redirect(url_for("tools.view_procrastination_sheet", sheet_id=sheet.id))

    if request.method == "POST":
        try:
            task_name = request.form.get("task_name", "").strip()
            avoidance_reason = request.form.get("avoidance_reason", "").strip() or None
            resistance_thoughts = request.form.get("resistance_thoughts", "").strip() or None
            tiny_step = request.form.get("tiny_step", "").strip()

            expected_difficulty_raw = request.form.get("expected_difficulty", "").strip()
            expected_satisfaction_raw = request.form.get("expected_satisfaction", "").strip()

            if not task_name:
                flash("Task name is required.", "error")
                return redirect(request.url)

            if not tiny_step:
                flash("Please add the smallest possible first step.", "error")
                return redirect(request.url)

            if not expected_difficulty_raw or not expected_satisfaction_raw:
                flash("Please complete both expected score fields.", "error")
                return redirect(request.url)

            expected_difficulty = int(expected_difficulty_raw)
            expected_satisfaction = int(expected_satisfaction_raw)

            if expected_difficulty < 0 or expected_difficulty > 10 or expected_satisfaction < 0 or expected_satisfaction > 10:
                flash("Scores must be between 0 and 10.", "error")
                return redirect(request.url)

            task = ProcrastinationTask(
                sheet_id=sheet.id,
                task_name=task_name,
                avoidance_reason=avoidance_reason,
                resistance_thoughts=resistance_thoughts,
                tiny_step=tiny_step,
                expected_difficulty=expected_difficulty,
                expected_satisfaction=expected_satisfaction
            )

            db.session.add(task)
            db.session.commit()

            flash("Task added to sheet.", "success")
            return redirect(url_for("tools.view_procrastination_sheet", sheet_id=sheet.id))

        except ValueError:
            db.session.rollback()
            flash("Score fields must be valid numbers.", "error")
            return redirect(request.url)

        except SQLAlchemyError:
            db.session.rollback()
            flash("Something went wrong while adding your task.", "error")
            return redirect(request.url)

        except Exception as e:
            db.session.rollback()
            print("ADD TASK ERROR:", e)
            flash("Unexpected error occurred. Please try again.", "error")
            return redirect(request.url)

    return render_template(
        "tools/add_procrastination_task.html",
        sheet=sheet,
        max_tasks=MAX_PROCRASTINATION_TASKS
    )


@tools.route("/tools/anti-procrastination/task/<int:task_id>/complete", methods=["GET", "POST"])
@login_required
def complete_procrastination_task(task_id):
    task = ProcrastinationTask.query.get_or_404(task_id)
    sheet = task.sheet

    if sheet.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        try:
            actual_difficulty_raw = request.form.get("actual_difficulty", "").strip()
            actual_satisfaction_raw = request.form.get("actual_satisfaction", "").strip()
            reflection = request.form.get("reflection", "").strip() or None

            if not actual_difficulty_raw or not actual_satisfaction_raw:
                flash("Please complete both actual score fields.", "error")
                return redirect(request.url)

            actual_difficulty = int(actual_difficulty_raw)
            actual_satisfaction = int(actual_satisfaction_raw)

            if actual_difficulty < 0 or actual_difficulty > 10 or actual_satisfaction < 0 or actual_satisfaction > 10:
                flash("Scores must be between 0 and 10.", "error")
                return redirect(request.url)

            task.actual_difficulty = actual_difficulty
            task.actual_satisfaction = actual_satisfaction
            task.reflection = reflection
            task.is_completed = True

            db.session.commit()

            flash("Task marked as complete.", "success")
            return redirect(url_for("tools.view_procrastination_sheet", sheet_id=sheet.id))

        except ValueError:
            db.session.rollback()
            flash("Score fields must be valid numbers.", "error")
            return redirect(request.url)

        except SQLAlchemyError:
            db.session.rollback()
            flash("Something went wrong while updating this task.", "error")
            return redirect(request.url)

        except Exception as e:
            db.session.rollback()
            print("COMPLETE TASK ERROR:", e)
            flash("Unexpected error occurred. Please try again.", "error")
            return redirect(request.url)

    return render_template(
        "tools/complete_procrastination_task.html",
        task=task,
        sheet=sheet
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