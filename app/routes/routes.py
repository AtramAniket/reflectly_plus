from flask import Blueprint, render_template
from flask_login import current_user, login_required


main = Blueprint("main", __name__)

@main.route("/dashboard")
@login_required
def dashboard():
    return f'Welcome {current_user.email}'