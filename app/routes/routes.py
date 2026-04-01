from datetime import datetime, timedelta
from flask_login import current_user, login_required
from app.services.ai_insights import generate_insight
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
    
    entries = sorted(current_user.entries, key=lambda x: x.created_at, reverse=True)

    total_entries = len(entries)

    mood_values = [e.mood_score for e in entries if e.mood_score is not None]

    avg_mood_score = round(sum(mood_values) / len(mood_values), 2) if mood_values else None

    dates = [e.created_at.strftime('%d %b %H:%M') for e in entries if e.mood_score is not None]

    one_week_ago = datetime.utcnow() - timedelta(days=7)

    entries_this_week = [e for e in entries if e.created_at and e.created_at >= one_week_ago]

    trend = 'Not enough data'

    if(len(mood_values) >= 3):
        if mood_values[-3:] > mood_values[:4]:
            trend = 'Improving 📈'
        elif mood_values[-3:] < mood_values[:4]:
            trend = 'Declining 📉'
        else:
            trend = 'Stable ➖'

    # generate AI insights using OpenAI API
    if entries:
        # insights = generate_insight(avg_mood_score, trend, entries)
        insights = 'This is a placeholder for AI Insights using OpenAI API'
    else:
        insights = 'Start Journalling to get insights'

    # Habits
    habits = current_user.habits


    return render_template('dashboard.html', 
        email=current_user.email, 
        journal_entries=entries,
        average_mood_score = avg_mood_score,
        total_entries=total_entries,
        entries_this_week = len(entries_this_week),
        trend = trend,
        dates=dates,
        moods = mood_values,
        insights = insights,
        habits = habits
        )