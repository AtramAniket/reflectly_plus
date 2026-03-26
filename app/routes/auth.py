from app.extensions import db
from app.models.user import User
from flask_login import login_user, logout_user
from flask import Blueprint, url_for, render_template, request, redirect, flash

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods = ['GET', 'POST'])
def signup():
	if request.method == 'POST':
		email = request.form.get('email')
		password = request.form.get('password')

		# basic validation
		if not email and password:
			flash('Email and password are required', 'error')
			return redirect(url_for('auth.signup'))

		# check if user exists
		existing_user = User.query.filter_by(email=email).first()
		if existing_user:
			flash('user already exists', 'error')
			return redirect(url_for('auth.signup'))

		# create a new user
		user = User(email=email)
		user.set_password(password)

		db.session.add(user)
		db.session.commit()

		flash('User created successfully', 'success')
		return redirect(url_for('auth.signup'))

	return render_template('signup.html')

@auth.route('/login', methods = ['GET', 'POST'])
def login():

	if request.method == 'POST':

		email = request.form.get('email')
		password = request.form.get('password')

		# check if user exists
		user = User.query.filter_by(email=email).first()
		if user and user.check_password(password):
			login_user(user)
			flash('User successfully logged in!', 'success')
			return redirect(url_for('main.dashboard'))
		else:
			flash('Invalid username or password', 'warning')
			return redirect(url_for('auth.login'))


	return render_template('login.html')


@auth.route('/logout')
def logout():
	logout_user()
	flash('user successfully logged out', 'success')
	return redirect(url_for('auth.login'))