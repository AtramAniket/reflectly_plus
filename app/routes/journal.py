import random
from datetime import datetime
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError
from app.models.journal import JournalEntry
from flask_login import current_user, login_required
from app.services.ai_insights import analyze_simple_journal
from app.models.journal_ai_analysis import JournalAIAnalysis
from app.forms.journal_forms import SimpleJournalForm
from flask import (
    Blueprint,
    url_for,
    render_template,
    request,
    redirect,
    flash,
    abort,
    current_app,
    jsonify,
)

journal = Blueprint('journal', __name__)


@journal.route('/journal/view_all', methods=['GET'])
@login_required
def view_all_entries():
    selected_type = request.args.get("type", "all")
    page = request.args.get("page", 1, type=int)

    base_query = JournalEntry.query.filter_by(user_id=current_user.id)

    total_entries = base_query.count()
    simple_count = base_query.filter_by(entry_type="simple").count()
    gratitude_count = base_query.filter_by(entry_type="gratitude").count()
    reflection_count = base_query.filter_by(entry_type="reflection").count()

    filtered_query = base_query

    if selected_type in ["simple", "gratitude", "reflection"]:
        filtered_query = filtered_query.filter_by(entry_type=selected_type)

    entries_pagination = (
        filtered_query
        .order_by(JournalEntry.created_at.desc())
        .paginate(page=page, per_page=6, error_out=False)
    )

    return render_template(
        'all_entries.html',
        entries=entries_pagination.items,
        pagination=entries_pagination,
        selected_type=selected_type,
        total_entries=total_entries,
        simple_count=simple_count,
        gratitude_count=gratitude_count,
        reflection_count=reflection_count
    )


@journal.route('/journal/create_new_entry/<entry_type>', methods=['GET', 'POST'])
@login_required
def create_new_entry(entry_type):
    if entry_type not in ['simple', 'gratitude', 'reflection']:
        abort(404)

    simple_form = SimpleJournalForm() if entry_type == "simple" else None

    if entry_type == "simple":
        if simple_form.validate_on_submit():
            try:
                new_entry = JournalEntry(
                    title=simple_form.title.data.strip(),
                    content=simple_form.content.data.strip(),
                    entry_type='simple',
                    mood_score=simple_form.mood_score.data,
                    user_id=current_user.id,
                    image_url=None
                )

                db.session.add(new_entry)
                db.session.commit()

                flash('New journal entry added successfully.', 'success')
                return redirect(url_for('journal.view_all_entries'))

            except SQLAlchemyError:
                db.session.rollback()
                current_app.logger.exception("Database error while saving simple journal entry")
                flash('Something went wrong while saving the entry. Please try again.', 'error')
                return redirect(request.url)

            except Exception:
                db.session.rollback()
                current_app.logger.exception("Unexpected error while creating simple journal entry")
                flash('An unexpected error occurred. Please try again later.', 'error')
                return redirect(request.url)

        if request.method == "POST":
            for errors in simple_form.errors.values():
                for error in errors:
                    flash(error, "error")

            return redirect(request.url)

        return render_template(
            'create_entry.html',
            entry_type=entry_type,
            simple_form=simple_form
        )

    if request.method == 'POST':
        from datetime import datetime

        mood_score_raw = request.form.get('mood_score', '').strip()
        image_url = None

        try:
            if not mood_score_raw:
                flash('Mood score is required.', 'error')
                return redirect(request.url)

            mood_score = int(mood_score_raw)

            if mood_score < 1 or mood_score > 10:
                flash('Mood score must be between 1 and 10.', 'error')
                return redirect(request.url)

            if entry_type == 'gratitude':
                gratitude_1 = request.form.get('gratitude_1', '').strip()
                gratitude_2 = request.form.get('gratitude_2', '').strip()
                gratitude_3 = request.form.get('gratitude_3', '').strip()

                if not all([gratitude_1, gratitude_2, gratitude_3]):
                    flash('Please answer all gratitude prompts.', 'error')
                    return redirect(request.url)

                structured_content = {
                    'gratitude_1': gratitude_1,
                    'gratitude_2': gratitude_2,
                    'gratitude_3': gratitude_3,
                }

                now = datetime.now()
                generated_title = (
                    f"Gratitude Journal Entry • "
                    f"{now.strftime('%A %B %d, %Y')} "
                    f"{now.strftime('%I:%M %p').lstrip('0')}"
                )

                new_entry = JournalEntry(
                    title=generated_title,
                    content=None,
                    structured_content=structured_content,
                    entry_type='gratitude',
                    mood_score=mood_score,
                    user_id=current_user.id,
                    image_url=image_url
                )

            else:
                went_well = request.form.get('went_well', '').strip()
                challenging = request.form.get('challenging', '').strip()
                tomorrow = request.form.get('tomorrow', '').strip()

                if not all([went_well, challenging, tomorrow]):
                    flash('Please answer all reflection prompts.', 'error')
                    return redirect(request.url)

                structured_content = {
                    'went_well': went_well,
                    'challenging': challenging,
                    'tomorrow': tomorrow,
                }

                now = datetime.now()
                generated_title = (
                    f"Daily Reflection Entry • "
                    f"{now.strftime('%A %B %d, %Y')} "
                    f"{now.strftime('%I:%M %p').lstrip('0')}"
                )

                new_entry = JournalEntry(
                    title=generated_title,
                    content=None,
                    structured_content=structured_content,
                    entry_type='reflection',
                    mood_score=mood_score,
                    user_id=current_user.id,
                    image_url=image_url
                )

            db.session.add(new_entry)
            db.session.commit()

            flash('New journal entry added successfully.', 'success')
            return redirect(url_for('journal.view_all_entries'))

        except ValueError:
            db.session.rollback()
            flash('Mood score must be a valid number.', 'error')
            return redirect(request.url)

        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("Database error while saving journal entry")
            flash('Something went wrong while saving the entry. Please try again.', 'error')
            return redirect(request.url)

        except Exception:
            db.session.rollback()
            current_app.logger.exception("Unexpected error while creating journal entry")
            flash('An unexpected error occurred. Please try again later.', 'error')
            return redirect(request.url)

    return render_template('create_entry.html', entry_type=entry_type)


@journal.route('/journal/entries/<int:entry_id>')
@login_required
def view_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)

    if entry.user_id != current_user.id:
        abort(403)

    analysis = entry.ai_analysis if entry.entry_type == "simple" else None

    can_regenerate = False
    if analysis and entry.updated_at:
        last_reflection_at = analysis.updated_at or analysis.created_at
        if last_reflection_at and entry.updated_at > last_reflection_at:
            can_regenerate = True

    return render_template(
        'view_entry.html',
        entry=entry,
        analysis=analysis,
        can_regenerate=can_regenerate
    )


@journal.route('/journal/entries/<int:entry_id>/generate-reflection', methods=['POST'])
@login_required
def generate_reflection(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)

    if entry.user_id != current_user.id:
        abort(403)

    if entry.entry_type != "simple":
        return jsonify({
            "ok": False,
            "message": "AI reflection is only available for simple journal entries."
        }), 400

    if not entry.content or not entry.content.strip():
        return jsonify({
            "ok": False,
            "message": "This entry has no content to analyze."
        }), 400

    force_regenerate = request.form.get("regenerate") == "true"

    existing_analysis = entry.ai_analysis

    if force_regenerate:
        if not existing_analysis:
            return jsonify({
                "ok": False,
                "message": "No existing reflection found to regenerate."
            }), 400

        if not entry.updated_at or not existing_analysis.created_at:
            return jsonify({
                "ok": False,
                "message": "Edit the journal entry before regenerating the reflection."
            }), 400

        if entry.updated_at <= existing_analysis.created_at:
            return jsonify({
                "ok": False,
                "message": "Reflection is already up to date."
            }), 400

    if existing_analysis and not force_regenerate:
        return jsonify({
            "ok": True,
            "cached": True,
            "analysis": {
                "summary": existing_analysis.summary,
                "tone": existing_analysis.tone,
                "distortions": existing_analysis.distortions or [],
                "reframe": existing_analysis.reframe,
                "assessment": existing_analysis.assessment,
                "created_at": (
                    existing_analysis.created_at.isoformat()
                    if existing_analysis.created_at else None
                ),
            }
        }), 200

    try:
        result = analyze_simple_journal(entry.content)

        distortions = result.get("distortions", [])
        if not isinstance(distortions, list):
            distortions = []

        if existing_analysis:
            existing_analysis.summary = result.get("summary", "")
            existing_analysis.tone = result.get("tone", "")
            existing_analysis.distortions = distortions
            existing_analysis.reframe = result.get("reframe", "")
            existing_analysis.assessment = result.get(
                "assessment",
                "balanced_reflection"
            )
            analysis = existing_analysis
        else:
            analysis = JournalAIAnalysis(
                entry_id=entry.id,
                entry_type="simple",
                summary=result.get("summary", ""),
                tone=result.get("tone", ""),
                distortions=distortions,
                reframe=result.get("reframe", ""),
                assessment=result.get("assessment", "balanced_reflection")
            )
            db.session.add(analysis)

        db.session.commit()

        return jsonify({
            "ok": True,
            "cached": False,
            "analysis": {
                "summary": analysis.summary,
                "tone": analysis.tone,
                "distortions": analysis.distortions or [],
                "reframe": analysis.reframe,
                "assessment": analysis.assessment,
                "created_at": (
                    analysis.created_at.isoformat()
                    if analysis.created_at else None
                ),
            }
        }), 200

    except Exception:
        db.session.rollback()
        current_app.logger.exception("AI reflection generation failed")
        return jsonify({
            "ok": False,
            "message": "Could not generate reflection right now. Please try again."
        }), 500


@journal.route('/journal/entries/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)

    if entry.user_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        title = request.form.get("title", "").strip()
        mood_score_raw = request.form.get("mood_score", "").strip()

        try:
            if not title:
                flash("Title is required.", "error")
                return redirect(request.url)

            if not mood_score_raw:
                flash("Mood score is required.", "error")
                return redirect(request.url)

            mood_score = int(mood_score_raw)

            if mood_score < 1 or mood_score > 10:
                flash("Mood score must be between 1 and 10.", "error")
                return redirect(request.url)

            entry.title = title
            entry.mood_score = mood_score

            if entry.entry_type == "simple":
                content = request.form.get("content", "").strip()

                if not content:
                    flash("Content is required for a simple journal entry.", "error")
                    return redirect(request.url)

                entry.content = content
                entry.structured_content = None

            elif entry.entry_type == "gratitude":
                gratitude_1 = request.form.get("gratitude_1", "").strip()
                gratitude_2 = request.form.get("gratitude_2", "").strip()
                gratitude_3 = request.form.get("gratitude_3", "").strip()

                if not all([gratitude_1, gratitude_2, gratitude_3]):
                    flash("Please answer all gratitude prompts.", "error")
                    return redirect(request.url)

                entry.content = None
                entry.structured_content = {
                    "gratitude_1": gratitude_1,
                    "gratitude_2": gratitude_2,
                    "gratitude_3": gratitude_3,
                }

            elif entry.entry_type == "reflection":
                went_well = request.form.get("went_well", "").strip()
                challenging = request.form.get("challenging", "").strip()
                tomorrow = request.form.get("tomorrow", "").strip()

                if not all([went_well, challenging, tomorrow]):
                    flash("Please answer all reflection prompts.", "error")
                    return redirect(request.url)

                entry.content = None
                entry.structured_content = {
                    "went_well": went_well,
                    "challenging": challenging,
                    "tomorrow": tomorrow,
                }

            db.session.commit()

            flash("Journal entry updated successfully.", "success")
            return redirect(url_for("journal.view_entry", entry_id=entry.id))

        except ValueError:
            db.session.rollback()
            flash("Mood score must be a valid number.", "error")
            return redirect(request.url)

        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("Database error while editing journal entry")
            flash("Something went wrong while updating your entry. Please try again.", "error")
            return redirect(request.url)

        except Exception:
            db.session.rollback()
            current_app.logger.exception("Unexpected error while editing journal entry")
            flash("Unexpected error occurred. Please try again.", "error")
            return redirect(request.url)

    return render_template(
        "edit_entry.html",
        entry=entry
    )


@journal.route('/journal/delete_article/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    entry = JournalEntry.query.get_or_404(entry_id)

    if entry.user_id != current_user.id:
        abort(403)

    db.session.delete(entry)
    db.session.commit()

    flash('Entry deleted successfully', 'success')
    return redirect(url_for('journal.view_all_entries'))