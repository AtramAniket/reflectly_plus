import calendar
from datetime import date, datetime, timedelta, timezone

from app.extensions import db
from app.models.habit import Habit
from app.models.habit_log import HabitLog
from flask_login import current_user, login_required
from flask import Blueprint, url_for, render_template, request, redirect, flash

habit = Blueprint('habit', __name__)

MAX_HABITS = 5
CALENDAR_DAYS = 35

ARCHIVE_REASON_OPTIONS = [
    "Too hard to maintain",
    "No longer relevant",
    "Replacing it with another habit",
    "Habit became routine",
    "Added by mistake",
    "This habit was stressing me out",
    "Other",
]


def get_current_streak(habit_id: int) -> int:
    streak = 0
    check_date = date.today()

    while True:
        log = HabitLog.query.filter_by(
            habit_id=habit_id,
            date=check_date,
            completed=True
        ).first()

        if not log:
            break

        streak += 1
        check_date -= timedelta(days=1)

    return streak


def get_longest_streak(habit_id: int) -> int:
    logs = HabitLog.query.filter_by(
        habit_id=habit_id,
        completed=True
    ).order_by(HabitLog.date.asc()).all()

    if not logs:
        return 0

    longest = 0
    current = 0
    previous_date = None

    for log in logs:
        if previous_date is None:
            current = 1
        elif log.date == previous_date + timedelta(days=1):
            current += 1
        elif log.date == previous_date:
            continue
        else:
            current = 1

        longest = max(longest, current)
        previous_date = log.date

    return longest

def get_month_navigation(year: int, month: int):
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    return (prev_year, prev_month), (next_year, next_month)


def build_month_calendar(habit, year: int, month: int):
    cal = calendar.Calendar(firstweekday=0)  # Monday
    today = date.today()

    habit_start_date = habit.created_at.date()

    month_start = date(year, month, 1)
    _, month_last_day = calendar.monthrange(year, month)
    month_end = date(year, month, month_last_day)

    completed_logs = HabitLog.query.filter(
        HabitLog.habit_id == habit.id,
        HabitLog.completed.is_(True),
        HabitLog.date >= month_start,
        HabitLog.date <= month_end
    ).all()

    completed_dates = {log.date for log in completed_logs}

    short_label = habit.name[:12] + "…" if len(habit.name) > 12 else habit.name

    weeks = []
    for week in cal.monthdatescalendar(year, month):
        week_cells = []

        for day in week:
            is_current_month = day.month == month
            is_before_creation = day < habit_start_date
            is_future = day > today
            is_completed = day in completed_dates
            is_missed = (
                is_current_month
                and not is_before_creation
                and not is_future
                and not is_completed
            )

            label = ""
            if is_completed:
                label = short_label
            elif is_missed:
                label = "Missed"

            week_cells.append({
                "date": day,
                "day_number": day.day,
                "weekday_label": day.strftime("%a"),
                "is_current_month": is_current_month,
                "is_today": day == today,
                "is_before_creation": is_before_creation,
                "is_future": is_future,
                "is_completed": is_completed,
                "is_missed": is_missed,
                "label": label,
            })

        weeks.append(week_cells)

    return weeks


def build_calendar_days(habit_id: int, habit_name: str, days: int = CALENDAR_DAYS):
    today = date.today()
    start_day = today - timedelta(days=days - 1)

    completed_logs = HabitLog.query.filter(
        HabitLog.habit_id == habit_id,
        HabitLog.completed.is_(True),
        HabitLog.date >= start_day,
        HabitLog.date <= today
    ).all()

    completed_dates = {log.date for log in completed_logs}

    short_label = habit_name[:12] + "…" if len(habit_name) > 12 else habit_name

    calendar_days = []
    for i in range(days):
        current_day = start_day + timedelta(days=i)
        is_future = current_day > today
        is_completed = current_day in completed_dates
        is_missed = (current_day < today) and (not is_completed)

        calendar_days.append({
            "date": current_day,
            "day_number": current_day.day,
            "weekday_label": current_day.strftime("%a"),
            "is_today": current_day == today,
            "is_completed": is_completed,
            "is_missed": is_missed,
            "is_future": is_future,
            "label": short_label if is_completed else ("Missed" if is_missed else ""),
        })

    return calendar_days


@habit.route('/habits', methods=['GET', 'POST'])
@login_required
def create_habit():
    active_habits = Habit.query.filter_by(
        user_id=current_user.id,
        is_archived=False
    ).order_by(Habit.id.desc()).all()

    archived_habits = Habit.query.filter_by(
        user_id=current_user.id,
        is_archived=True
    ).order_by(Habit.archived_at.desc()).all()

    habit_count = len(active_habits)
    at_limit = habit_count >= MAX_HABITS

    if request.method == 'POST':
        if at_limit:
            flash(f'You can track up to {MAX_HABITS} habits at a time.', 'warning')
            return redirect(url_for('habit.create_habit'))

        name = request.form.get('name', '').strip()

        if not name:
            flash('Please enter a habit name.', 'warning')
            return redirect(url_for('habit.create_habit'))

        new_habit = Habit(
            name=name,
            user_id=current_user.id
        )

        db.session.add(new_habit)
        db.session.commit()

        flash('Habit added successfully.', 'success')
        return redirect(url_for('habit.create_habit', habit_id=new_habit.id))

    today_completed_logs = HabitLog.query.join(Habit).filter(
        Habit.user_id == current_user.id,
        Habit.is_archived.is_(False),
        HabitLog.date == date.today(),
        HabitLog.completed.is_(True)
    ).all()

    today_logs = {log.habit_id for log in today_completed_logs}

    habit_streaks = {}
    habit_best_streaks = {}

    for h in active_habits:
        habit_streaks[h.id] = get_current_streak(h.id)
        habit_best_streaks[h.id] = get_longest_streak(h.id)

    completed_today_count = len(today_logs)
    longest_streak_overall = max(habit_best_streaks.values(), default=0)
    current_best_streak = max(habit_streaks.values(), default=0)

    selected_habit_id = request.args.get('habit_id', type=int)

    today = date.today()
    selected_year = request.args.get('year', type=int) or today.year
    selected_month = request.args.get('month', type=int) or today.month

    selected_habit = None
    if active_habits:
        if selected_habit_id:
            selected_habit = next((h for h in active_habits if h.id == selected_habit_id), None)
        if selected_habit is None:
            selected_habit = active_habits[0]

    calendar_weeks = []
    month_label = ""
    prev_year = prev_month = next_year = next_month = None

    if selected_habit:
        calendar_weeks = build_month_calendar(selected_habit, selected_year, selected_month)
        month_label = date(selected_year, selected_month, 1).strftime("%B %Y")
        (prev_year, prev_month), (next_year, next_month) = get_month_navigation(selected_year, selected_month)

    return render_template(
        'create_habit.html',
        habits=active_habits,
        archived_habits=archived_habits,
        today_logs=today_logs,
        habit_streaks=habit_streaks,
        habit_best_streaks=habit_best_streaks,
        habit_count=habit_count,
        completed_today_count=completed_today_count,
        longest_streak_overall=longest_streak_overall,
        current_best_streak=current_best_streak,
        max_habits=MAX_HABITS,
        at_limit=at_limit,
        selected_habit=selected_habit,
        archive_reason_options=ARCHIVE_REASON_OPTIONS,
        selected_year=selected_year,
        selected_month=selected_month,
        calendar_weeks=calendar_weeks,
        month_label=month_label,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
    )


@habit.route('/habits/<int:habit_id>/complete')
@login_required
def complete_habit(habit_id):
    target_habit = Habit.query.filter_by(
        id=habit_id,
        user_id=current_user.id,
        is_archived=False
    ).first_or_404()

    existing_log = HabitLog.query.filter_by(
        habit_id=target_habit.id,
        date=date.today()
    ).first()

    if existing_log:
        flash('You already marked this habit as done today.', 'info')
        return redirect(url_for('habit.create_habit', habit_id=target_habit.id))

    log = HabitLog(
        habit_id=target_habit.id,
        completed=True
    )

    db.session.add(log)
    db.session.commit()

    flash('Habit marked as done successfully!', 'success')
    return redirect(url_for('habit.create_habit', habit_id=target_habit.id))


@habit.route('/habits/<int:habit_id>/archive', methods=['POST'])
@login_required
def archive_habit(habit_id):
    target_habit = Habit.query.filter_by(
        id=habit_id,
        user_id=current_user.id,
        is_archived=False
    ).first_or_404()

    reason = request.form.get('archive_reason', '').strip()
    note = request.form.get('archive_note', '').strip()

    if reason not in ARCHIVE_REASON_OPTIONS:
        flash('Please choose a valid reason for removing the habit.', 'warning')
        return redirect(url_for('habit.create_habit', habit_id=habit_id))

    target_habit.is_archived = True
    target_habit.archived_at = datetime.now(timezone.utc)
    target_habit.archived_reason = reason
    target_habit.archived_note = note or None

    db.session.commit()

    flash('Habit removed from active tracking.', 'success')
    return redirect(url_for('habit.create_habit'))