from datetime import date
from app.extensions import db
from app.models.habit import Habit
from app.models.habit_log import HabitLog
from flask_login import current_user, login_required
from flask import Blueprint, url_for, render_template, request, redirect, flash

habit = Blueprint('habit', __name__)

@habit.route('/habits/create', methods=['GET', 'POST'])
@login_required
def create_habit():
	if request.method == 'POST':
		
		name = request.form.get('name')

		if name:

			new_habit = Habit(
				name=name,
				user_id=current_user.id)

			db.session.add(new_habit)
			db.session.commit()

			flash('Habit added successfully', 'success')
			return redirect(url_for('main.dashboard'))

	return render_template('create_habit.html')

@habit.route('/habits/<int:habit_id>/complete')
@login_required
def complete_habit(habit_id):

	existing_log = HabitLog.query.filter_by(
	    habit_id=habit_id,
	    date=date.today()
	).first()

	if not existing_log:
		log = HabitLog(
			habit_id = habit_id,
			completed=True)

		db.session.add(log)
		db.session.commit()

		flash('Habit marked as done successfully!', 'success')

	return redirect(url_for('main.dashboard'))