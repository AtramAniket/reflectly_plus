import random
from app.extensions import db
from sqlalchemy.exc import SQLAlchemyError
from app.models.journal import JournalEntry
from flask_login import current_user, login_required
from flask import Blueprint, url_for, render_template, request, redirect, flash, abort, current_app

journal = Blueprint('journal', __name__)

@journal.route('/journal/view_all', methods=['GET'])
@login_required
def view_all_entries():

	entries = JournalEntry.query.filter_by(user_id=current_user.id).order_by(JournalEntry.created_at.desc()).all()

	return render_template('all_entries.html', entries = entries)


@journal.route('/journal/create_new_entry/<entry_type>', methods=['GET', 'POST'])
@login_required
def create_new_entry(entry_type):

	if entry_type not in ['simple', 'gratitude', 'reflection']:
		abort(404)

	if request.method == 'POST':

		# Title and Mood Score
		title = request.form.get('title', '').strip()
		mood_score = request.form.get('mood_score', '').strip()

		# Image
		image_id = random.randint(1, 700)
		image_url = f"https://picsum.photos/id/{image_id}/1200/400"

		try: 

			if not title:
				flash('Tile is required and cannot be empty', 'error')
				return redirect(request.url)

			if not mood_score:
				flash('Mood score is required.', 'error')
				return redirect(request.url)

			if int(mood_score) < 0 or int(mood_score) > 10:
				flash('Mood score must be between 0 and 10', 'error')
				return redirect(request.url)

			# SIMPLE JOURNAL ENTRY
			if entry_type == 'simple':
			
				content = request.form.get('content')

				if not content:
					flash('Content is required to save journal entry.', 'error')
					return redirect(request.url)

				new_entry = JournalEntry(
					title = title,
					content = content,
					entry_type = 'simple',
					mood_score = mood_score,
					user_id = current_user.id,
					image_url = image_url
					)

			# GRATITUDE JOURNAL ENTRY
			elif entry_type == 'gratitude':

				gratitude_1 = request.form.get('gratitude_1')
				gratitude_2 = request.form.get('gratitude_2')
				gratitude_3 = request.form.get('gratitude_3')

				if not all([gratitude_1, gratitude_2, gratitude_3]):
					flash('Please answer all questions', 'error')
					return redirect(request.url)

				structured_content = {
					'gratitude_1': gratitude_1,
					'gratitude_2': gratitude_2,
					'gratitude_3': gratitude_3,
				}


				new_entry = JournalEntry(
					title = title,
					content=None,
					structured_content = structured_content,
					entry_type = 'gratitude',
					mood_score = mood_score,
					user_id = current_user.id,
					image_url = image_url
					)

			# DAILY REFLECTION JOURNAL ENTRY
			elif entry_type == 'reflection':

				went_well = request.form.get('went_well')
				challenging = request.form.get('challenging')
				tomorrow = request.form.get('tomorrow')

				if not all([went_well, challenging, tomorrow]):
					flash('Please answer all reflection prompts', 'error')
					return redirect(request.url)

				structured_content = {
					'went_well': request.form.get('went_well'),
					'challenging': request.form.get('challenging'),
					'tomorrow': request.form.get('tomorrow'),
				}

				new_entry = JournalEntry(
					title = title,
					content=None,
					structured_content = structured_content,
					entry_type = 'reflection',
					mood_score = mood_score,
					user_id = current_user.id,
					image_url = image_url
					)

			db.session.add(new_entry)
			db.session.commit()

			flash('New Journal entry added successfully', 'success')
			return redirect(url_for('main.dashboard'))

		except ValueError:
			db.session.rollback()
			flash('Mood score must be valid number.', 'error')
			return(redirect(request.url))

		except SQLAlchemyError:
			db.session.rollback()
			flash('Something went wrong while saving entry, please try again.', 'error')
			return(redirect(request.url))

		except Exception:
			db.session.rollback()
			flash('Unexpected error occured. Please try again later.', 'error')
			return(redirect(request.url))

	return render_template('create_entry.html', entry_type=entry_type)


@journal.route('/entries/<int:entry_id>')
@login_required
def view_entry(entry_id):
	
    entry = JournalEntry.query.get_or_404(entry_id)

    if entry.user_id != current_user.id:
        abort(403)

    return render_template('view_entry.html', entry=entry)



@journal.route('/entries/<int:entry_id>/edit', methods=['GET', 'POST'])
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

            # SIMPLE JOURNAL
            if entry.entry_type == "simple":
                content = request.form.get("content", "").strip()

                if not content:
                    flash("Content is required for a simple journal entry.", "error")
                    return redirect(request.url)

                entry.content = content
                entry.structured_content = None

            # GRATITUDE JOURNAL
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

            # REFLECTION JOURNAL
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
        "journal/edit_entry.html",
        entry=entry
    )


@journal.route('/journal/delete_article/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def delete_entry(entry_id):

	entry = JournalEntry.query.get_or_404(entry_id) 

	if entry.user_id != current_user.id:
		abort(403)

	db.session.delete(entry)
	db.session.commit()

	flash('Entry deleted successfully', 'success')
	return redirect(url_for('main.dashboard'))

	return render_template('edit_entry.html', journal_entry = entry)