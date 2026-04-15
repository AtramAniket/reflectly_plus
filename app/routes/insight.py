from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.helpers.weekly_insights_helper import get_or_generate_weekly_insight

insights_bp = Blueprint("insights", __name__)

@insights_bp.route("/insights")
@login_required
def insights():
    insight = get_or_generate_weekly_insight(current_user)
    return render_template("insights.html", insight=insight)