from datetime import datetime, timedelta, date

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

from app.models.habit import Habit
from app.models.habit_log import HabitLog
from app.models.journal import JournalEntry
from app.services.ai_insights import generate_insight

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

    one_week_ago = datetime.utcnow() - timedelta(days=7)
    entries_this_week = [e for e in all_entries if e.created_at and e.created_at >= one_week_ago]

    trend = 'Not enough data'
    if len(mood_values) >= 3:
        if mood_values[-3:] > mood_values[:4]:
            trend = 'Improving 📈'
        elif mood_values[-3:] < mood_values[:4]:
            trend = 'Declining 📉'
        else:
            trend = 'Stable ➖'

    if all_entries:
        # insights = generate_insight(avg_mood_score, trend, all_entries)
        insights = 'This is a placeholder for AI Insights using OpenAI API'
    else:
        insights = 'Start Journalling to get insights'

    # Active habits only
    habits = (
        Habit.query
        .filter_by(user_id=current_user.id, is_archived=False)
        .order_by(Habit.id.desc())
        .all()
    )

    # Today's completed logs for this user's active habits only
    today_logs = {
        log.habit_id
        for log in HabitLog.query.join(Habit).filter(
            Habit.user_id == current_user.id,
            Habit.is_archived.is_(False),
            HabitLog.date == date.today(),
            HabitLog.completed.is_(True)
        ).all()
    }

    # Streaks for active habits only
    habit_streaks = {}
    for habit in habits:
        active_logs = [log for log in habit.logs if log.completed]
        habit_streaks[habit.id] = calculate_streaks(active_logs)

    return render_template(
        'dashboard.html',
        email=current_user.email,
        journal_entries=recent_entries,
        average_mood_score=avg_mood_score,
        total_entries=total_entries,
        entries_this_week=len(entries_this_week),
        trend=trend,
        dates=dates,
        moods=mood_values,
        insights=insights,
        habits=habits,
        today_logs=today_logs,
        habit_streaks=habit_streaks
    )