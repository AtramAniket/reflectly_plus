from sqlalchemy.exc import SQLAlchemyError
from flask_login import login_required, current_user
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from app.extensions import db
from app.models.mood_checklist import MoodChecklistResult
from app.models.procrastination_sheet import ProcrastinationSheet
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
            task_name = request.form.get("task_name", "").strip()
            avoidance_reason = request.form.get("avoidance_reason", "").strip() or None
            resistance_thoughts = request.form.get("resistance_thoughts", "").strip() or None
            tiny_step = request.form.get("tiny_step", "").strip()
            reflection = request.form.get("reflection", "").strip() or None

            expected_difficulty_raw = request.form.get("expected_difficulty", "").strip()
            expected_satisfaction_raw = request.form.get("expected_satisfaction", "").strip()
            actual_difficulty_raw = request.form.get("actual_difficulty", "").strip()
            actual_satisfaction_raw = request.form.get("actual_satisfaction", "").strip()

            if not task_name:
                flash("Task name is required.", "error")
                return redirect(request.url)

            if not tiny_step:
                flash("Please add the smallest possible first step.", "error")
                return redirect(request.url)

            if not all([
                expected_difficulty_raw,
                expected_satisfaction_raw,
                actual_difficulty_raw,
                actual_satisfaction_raw
            ]):
                flash("Please complete all score fields.", "error")
                return redirect(request.url)

            expected_difficulty = int(expected_difficulty_raw)
            expected_satisfaction = int(expected_satisfaction_raw)
            actual_difficulty = int(actual_difficulty_raw)
            actual_satisfaction = int(actual_satisfaction_raw)

            score_values = [
                expected_difficulty,
                expected_satisfaction,
                actual_difficulty,
                actual_satisfaction
            ]

            if any(score < 0 or score > 10 for score in score_values):
                flash("All scores must be between 0 and 10.", "error")
                return redirect(request.url)

            sheet = ProcrastinationSheet(
                user_id=current_user.id,
                task_name=task_name,
                avoidence_reason=avoidance_reason,
                expected_difficulty=expected_difficulty,
                expected_statisfaction=expected_satisfaction,
                resistance_thoughts=resistance_thoughts,
                tiny_steps=tiny_step,
                actual_difficulty=actual_difficulty,
                actual_statisfaction=actual_satisfaction,
                reflection=reflection
            )

            db.session.add(sheet)
            db.session.commit()

            flash("Anti-procrastination sheet saved successfully.", "success")
            return redirect(url_for("tools.view_procrastination_sheet", sheet_id=sheet.id))

        except ValueError:
            db.session.rollback()
            flash("All score fields must be valid numbers.", "error")
            return redirect(request.url)

        except SQLAlchemyError:
            db.session.rollback()
            flash("Something went wrong while saving your sheet.", "error")
            return redirect(request.url)

        except Exception as e:
            db.session.rollback()
            flash(f"Unexpected error occurred. Please try again", "error")
            return redirect(request.url)

    return render_template("tools/anti_procrastination.html")

@tools.route("/tools/anti-procrastination/<int:sheet_id>")
@login_required
def view_procrastination_sheet(sheet_id):
    sheet = ProcrastinationSheet.query.get_or_404(sheet_id)

    if sheet.user_id != current_user.id:
        abort(403)

    return render_template(
        "tools/view_procrastination_sheet.html",
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
        sheets=sheets
    )