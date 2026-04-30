from datetime import datetime, timedelta, date, timezone

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

from app.models.habit import Habit
from app.models.habit_log import HabitLog
from app.models.journal import JournalEntry
from app.helper.illustrations_helper import build_scene_payload
from app.models.weekly_insight import WeeklyInsight
from app.helper.weekly_insights_helper import build_insight_response

main = Blueprint("main", __name__)


def calculate_streaks(logs):
    if not logs:
        return 0

    logs = sorted(logs, key=lambda x: x.date, reverse=True)

    streaks = 0
    current_day = date.today()

    for log in logs:
        if log.completed and log.date == current_day:
            streaks += 1
            current_day -= timedelta(days=1)
        else:
            break

    return streaks


@main.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main.route("/logs")
@login_required
def logs():
    return render_template("logs.html")


@main.route("/dashboard")
@login_required
def dashboard():
    all_entries = (
        JournalEntry.query
        .filter_by(user_id=current_user.id)
        .order_by(JournalEntry.created_at.asc())
        .all()
    )

    recent_entries = (
        JournalEntry.query
        .filter_by(user_id=current_user.id)
        .order_by(JournalEntry.created_at.desc())
        .limit(3)
        .all()
    )

    total_entries = len(all_entries)

    mood_values = [e.mood_score for e in all_entries if e.mood_score is not None]
    avg_mood_score = round(sum(mood_values) / len(mood_values), 2) if mood_values else None
    dates = [e.created_at.strftime('%d %b %H:%M') for e in all_entries if e.mood_score is not None]

    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    entries_this_week_count = (
        JournalEntry.query
        .filter(
            JournalEntry.user_id == current_user.id,
            JournalEntry.created_at >= one_week_ago
        )
        .count()
    )

    trend = 'Not enough data'
    if len(mood_values) >= 3:
        if mood_values[-3:] > mood_values[:4]:
            trend = 'Improving 📈'
        elif mood_values[-3:] < mood_values[:4]:
            trend = 'Declining 📉'
        else:
            trend = 'Stable ➖'

    if all_entries:
        insights = 'This is a placeholder for AI Insights using OpenAI API'
    else:
        insights = 'Start Journalling to get insights'

    habits = (
        Habit.query
        .filter_by(user_id=current_user.id, is_archived=False)
        .order_by(Habit.id.desc())
        .all()
    )

    today_logs = {
        log.habit_id
        for log in HabitLog.query.join(Habit).filter(
            Habit.user_id == current_user.id,
            Habit.is_archived.is_(False),
            HabitLog.date == date.today(),
            HabitLog.completed.is_(True)
        ).all()
    }

    habit_streaks = {}
    for habit in habits:
        active_logs = [log for log in habit.logs if log.completed]
        habit_streaks[habit.id] = calculate_streaks(active_logs)

    active_habits_count = (
        Habit.query
        .filter_by(user_id=current_user.id, is_archived=False)
        .order_by(Habit.id.desc())
        .all()
    )

    dashboard_scene = build_scene_payload(score=avg_mood_score, seed_value=f'dashboard-{current_user.id}')

    latest_weekly_insight_record = (
        WeeklyInsight.query
        .filter_by(user_id=current_user.id)
        .order_by(WeeklyInsight.week_start.desc())
        .first()
    )

    latest_weekly_insight = (
        build_insight_response(latest_weekly_insight_record)
        if latest_weekly_insight_record
        else None
    )

    dashboard_patterns = []
    dashboard_suggestions = []

    weekly_insight_status = "ready" if latest_weekly_insight else "no_data"
    weekly_insight_message = {
        "title": "Your weekly insight is ready",
        "body": "Review the patterns and suggestions generated from your recent activity.",
        "icon": "sparkles",
    }

    if latest_weekly_insight:
        dashboard_patterns = latest_weekly_insight.get("patterns", [])[:3]
        dashboard_suggestions = latest_weekly_insight.get("suggestions", [])[:3]
    elif entries_this_week_count > 0:
        weekly_insight_status = "insufficient"
        weekly_insight_message = {
            "title": "Weekly insight is warming up",
            "body": "Add a few more journal entries, mood check-ins, or habit logs this week to unlock a stronger weekly reflection.",
            "icon": "seedling",
        }
    else:
        weekly_insight_status = "no_data"
        weekly_insight_message = {
            "title": "Start this week's story",
            "body": "Once you add some activity this week, Reflectly can prepare a meaningful weekly insight for you.",
            "icon": "book-heart",
        }

    return render_template(
        'dashboard.html',
        email=current_user.email,
        journal_entries=recent_entries,
        average_mood_score=avg_mood_score,
        total_entries=total_entries,
        entries_this_week=entries_this_week_count,
        trend=trend,
        dates=dates,
        moods=mood_values,
        insights=insights,
        habits=habits,
        today_logs=today_logs,
        habit_streaks=habit_streaks,
        dashboard_scene=dashboard_scene,
        latest_weekly_insight=latest_weekly_insight,
        dashboard_patterns=dashboard_patterns,
        dashboard_suggestions=dashboard_suggestions,
        weekly_insight_status=weekly_insight_status,
        weekly_insight_message=weekly_insight_message,
        active_habits_count=len(active_habits_count)
    )