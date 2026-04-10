from sqlalchemy.exc import SQLAlchemyError
from flask_login import login_required, current_user
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from app.extensions import db
from app.models.mood_checklist import MoodChecklistResult
from app.helper.mood_wellbeing_check import get_checklist_feedback

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