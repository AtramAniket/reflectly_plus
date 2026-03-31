from datetime import datetime, timedelta
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
    
    entries = sorted(current_user.entries, key=lambda x: x.created_at, reverse=True)

    total_entries = len(entries)

    mood_values = [e.mood_score for e in entries if e.mood_score is not None]

    avg_mood_score = round(sum(mood_values) / len(mood_values), 2) if mood_values else None

    one_week_ago = datetime.utcnow() - timedelta(days=7)

    entries_this_week = [e for e in entries if e.created_at and e.created_at >= one_week_ago]


    return render_template('dashboard.html', 
        email=current_user.email, 
        journal_entries=entries,
        average_mood_score = avg_mood_score,
        total_entries=total_entries,
        entries_this_week = len(entries_this_week)
        )