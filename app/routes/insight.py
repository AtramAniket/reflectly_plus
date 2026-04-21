from datetime import datetime, timedelta

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from app.helper.illustrations_helper import build_scene_payload
from app.helper.weekly_insights_helper import (
    get_or_generate_weekly_insight,
    get_user_timezone,
    get_week_range_for_user,
)

insight = Blueprint("insights", __name__)


@insight.route("/insights")
@login_required
def home():
    """
    Render the weekly Insights page for the requested week.

    Query params:
    - week_start: optional ISO date (YYYY-MM-DD) used to navigate to a past week

    Behavior:
    - resolves the target week
    - loads or generates that week's insight payload
    - computes previous/next week navigation
    - builds a soft illustration scene based on the week's average mood signal
    """
    week_start_param = request.args.get("week_start")
    target_date = None

    if week_start_param:
        target_date = datetime.strptime(week_start_param, "%Y-%m-%d").date()

    insight_payload = get_or_generate_weekly_insight(
        current_user,
        target_date=target_date,
    )

    prev_week_start = (insight_payload["week_start"] - timedelta(days=7)).isoformat()

    current_week_start, _ = get_week_range_for_user(current_user)
    next_week_start = None

    if insight_payload["week_start"] < current_week_start:
        next_week_start = (
            insight_payload["week_start"] + timedelta(days=7)
        ).isoformat()

    avg_mood_score = (
        insight_payload.get("structured_context", {})
        .get("mood", {})
        .get("avg_score")
    )

    scene_score = avg_mood_score if avg_mood_score is not None else 5

    insight_scene = build_scene_payload(
        score=scene_score,
        seed_value=f"insight-{current_user.id}-{insight_payload['week_start']}",
    )

    return render_template(
        "weekly_insights/insights.html",
        insight=insight_payload,
        prev_week_start=prev_week_start,
        next_week_start=next_week_start,
        insight_scene=insight_scene,
    )