from flask_login import current_user, login_required
from flask import Blueprint, render_template, redirect, url_for



main = Blueprint("main", __name__)

@main.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    else:
        return redirect(url_for('auth.login'))

@main.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html', email=current_user.email)