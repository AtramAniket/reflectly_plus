from flask import Blueprint, render_template
from flask_login import current_user, login_required

from app.helper.weekly_insights_helper import get_or_generate_weekly_insight

insight = Blueprint("insights", __name__)

@insight.route("/insights")
@login_required
def insights():
    insight = get_or_generate_weekly_insight(current_user)
    return render_template("weekly_insights/insights.html", insight=insight)