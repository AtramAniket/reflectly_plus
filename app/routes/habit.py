from app.extensions import db
from app.models.habit import Habit
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