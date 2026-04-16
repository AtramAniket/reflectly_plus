from datetime import datetime, timedelta
from flask_login import current_user, login_required
from flask import Blueprint, render_template, request

from app.helper.weekly_insights_helper import get_or_generate_weekly_insight,get_user_timezone,get_week_range_for_user

insight = Blueprint("insights", __name__)

@insight.route("/insights")
@login_required
def insights():
    week_start_param = request.args.get("week_start")
    target_date = None

    if week_start_param:
        target_date = datetime.strptime(week_start_param, "%Y-%m-%d").date()

    insight = get_or_generate_weekly_insight(current_user, target_date=target_date)

    prev_week_start = (insight["week_start"] - timedelta(days=7)).isoformat()

    today_local = datetime.now(get_user_timezone(current_user)).date()
    current_week_start, _ = get_week_range_for_user(current_user)

    next_week_start = None
    if insight["week_start"] < current_week_start:
        next_week_start = (insight["week_start"] + timedelta(days=7)).isoformat()

    return render_template(
        "weekly_insights/insights.html",
        insight=insight,
        prev_week_start=prev_week_start,
        next_week_start=next_week_start,
    )