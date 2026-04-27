from app.extensions import db
from app.models.user import User
from app.forms.auth_form import SignupForm, LoginForm

from flask_login import login_user, logout_user, current_user
from flask import Blueprint, url_for, render_template, redirect, flash
from sqlalchemy import or_


auth = Blueprint('auth', __name__)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():

    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = SignupForm()

    if form.validate_on_submit():
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower()
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash('Your account has been created. Please log in to continue.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('signup.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        identifier = form.identifier.data.strip().lower()

        user = User.query.filter(
            or_(
                User.email == identifier,
                User.username == identifier
            )
        ).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f'Welcome back, {user.username}.', 'success')
            return redirect(url_for('main.dashboard'))

        flash('Invalid email/username or password.', 'warning')

    return render_template('login.html', form=form)


@auth.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))