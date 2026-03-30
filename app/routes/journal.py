from app.extensions import db
from app.models.journal import JournalEntry
from flask_login import current_user, login_required
from flask import Blueprint, url_for, render_template, request, redirect, flash, abort

journal = Blueprint('journal', __name__)

@journal.route('/journal/create_new_entry', methods=['GET', 'POST'])
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

@journal.route('/journal/edit/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):

	entry = JournalEntry.query.get_or_404(entry_id) 

	if entry.user_id != current_user.id:
		abort(403)


	if request.method == 'POST':

		entry.title = request.form.get('title')
		entry.content = request.form.get('content')
		entry.mood_score = request.form.get('mood_score') or 0

		db.session.commit()

		flash('Entry updated successfully', 'success')
		return redirect(url_for('main.dashboard'))

	return render_template('edit_entry.html', journal_entry = entry)

@journal.route('/journal/delete_article/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):

	entry = JournalEntry.query.get_or_404(entry_id) 

	if entry.user_id != current_user.id:
		abort(403)


	if request.method == 'POST':

		db.session.delete(entry)
		db.session.commit()

		flash('Entry deleted successfully', 'success')
		return redirect(url_for('main.dashboard'))

	return render_template('edit_entry.html', journal_entry = entry)