from app.extensions import db
from app.models.journal import JournalEntry
from flask_login import current_user, login_required
from flask import Blueprint, url_for, render_template, request, redirect, flash

journal = Blueprint('journal', __name__)

@journal.route('/create_new_entry', methods=['GET', 'POST'])
@login_required
def create_new_entry():
	if request.method == 'POST':
		
		title = request.form.get('title')
		content = request.form.get('content')
		mood_score = request.form.get('mood_score')

		new_entry = JournalEntry(
			title = title,
			content = content,
			mood_score = mood_score,
			user_id = current_user.id
			)

		db.session.add(new_entry)
		db.session.commit()

		flash('New Journal entry added successfully', 'success')
		return redirect(url_for('main.dashboard'))

	return render_template('create_entry.html')