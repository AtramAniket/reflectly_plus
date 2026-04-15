from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from statistics import mean
from typing import Any, Optional

from sqlalchemy import and_

from app.extensions import db
from app.models import WeeklyInsight

# Replace these imports with your real models
# from app.models import JournalEntry, MoodEntry, Habit, HabitLog, ProcrastinationSheet, ProcrastinationTask


def get_or_generate_weekly_insight(user, target_date: Optional[date] = None) -> dict[str, Any]:
    """
    Main entry point for the Insights page.

    Flow:
    1. Compute week range
    2. Return cached insight if it already exists
    3. Build structured weekly context
    4. Run sufficiency + contradiction checks
    5. Save fallback if insufficient data
    6. Otherwise generate AI summary and save it
    7. Return normalized payload for route/template use
    """
    week_start, week_end = get_week_range(target_date)

    existing_insight = WeeklyInsight.query.filter_by(
        user_id=user.id,
        week_start=week_start,
    ).first()

    if existing_insight:
        return build_insight_response(existing_insight)

    context = build_weekly_context(user_id=user.id, week_start=week_start, week_end=week_end)
    sufficiency = check_insight_sufficiency(context)
    contradiction_flag = detect_contradictions(context)
    cross_signal_patterns = build_cross_signal_patterns(context)

    if sufficiency["level"] == "insufficient":
        saved_insight = save_insufficient_insight(
            user_id=user.id,
            week_start=week_start,
            week_end=week_end,
            context=context,
            contradiction_flag=contradiction_flag,
            sufficiency=sufficiency,
        )
        return build_insight_response(saved_insight)

    ai_output = generate_ai_weekly_insight(
        context=context,
        sufficiency=sufficiency,
        contradiction_flag=contradiction_flag,
        cross_signal_patterns=cross_signal_patterns,
    )

    saved_insight = save_generated_insight(
        user_id=user.id,
        week_start=week_start,
        week_end=week_end,
        context=context,
        sufficiency=sufficiency,
        contradiction_flag=contradiction_flag,
        cross_signal_patterns=cross_signal_patterns,
        ai_output=ai_output,
    )

    return build_insight_response(saved_insight)


def get_week_range(target_date: Optional[date] = None) -> tuple[date, date]:
    """
    Returns Monday-Sunday for the given date.
    """
    target_date = target_date or date.today()
    week_start = target_date - timedelta(days=target_date.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def build_weekly_context(user_id: int, week_start: date, week_end: date) -> dict[str, Any]:
    """
    Builds the full structured weekly context used for both local UI and AI generation.
    """
    journal_data = aggregate_journal_data(user_id=user_id, week_start=week_start, week_end=week_end)
    mood_data = aggregate_mood_data(user_id=user_id, week_start=week_start, week_end=week_end)
    habits_data = aggregate_habit_data(user_id=user_id, week_start=week_start, week_end=week_end)
    procrastination_data = aggregate_procrastination_data(
        user_id=user_id,
        week_start=week_start,
        week_end=week_end,
    )

    active_days = calculate_active_days(
        journal_dates=journal_data["entry_dates"],
        mood_dates=mood_data["entry_dates"],
        habit_dates=habits_data["log_dates"],
        procrastination_dates=procrastination_data["task_dates"],
    )

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "journal": {
            "count": journal_data["count"],
            "types": journal_data["types"],
            "avg_length": journal_data["avg_length"],
            "top_keywords": journal_data["top_keywords"],
            "tone_distribution": journal_data["tone_distribution"],
            "distortions": journal_data["distortions"],
        },
        "mood": {
            "entries": mood_data["entries"],
            "avg_score": mood_data["avg_score"],
            "variance": mood_data["variance"],
            "min_score": mood_data["min_score"],
            "max_score": mood_data["max_score"],
            "trend": mood_data["trend"],
        },
        "habits": {
            "active": habits_data["active"],
            "completed_logs": habits_data["completed_logs"],
            "completion_rate": habits_data["completion_rate"],
        },
        "procrastination": {
            "tasks": procrastination_data["tasks"],
            "completed": procrastination_data["completed"],
            "completion_rate": procrastination_data["completion_rate"],
        },
        "activity": {
            "active_days": active_days,
            "inactive_days": max(0, 7 - active_days),
        },
    }


def check_insight_sufficiency(context: dict[str, Any]) -> dict[str, Any]:
    """
    Conservative gating so the AI is only called when signal is meaningful enough.
    """
    journal_count = context["journal"]["count"]
    mood_count = context["mood"]["entries"]
    habit_logs = context["habits"]["completed_logs"]
    procrastination_completed = context["procrastination"]["completed"]
    active_days = context["activity"]["active_days"]

    total_actions = journal_count + mood_count + habit_logs + procrastination_completed

    level = "insufficient"
    confidence = "low"
    reasons: list[str] = []

    if journal_count >= 3 or mood_count >= 4 or total_actions >= 5:
        level = "basic"
        confidence = "low"
        reasons.append("Minimum weekly activity threshold met.")

    if journal_count >= 4 and mood_count >= 4 and active_days >= 3:
        level = "moderate"
        confidence = "medium"
        reasons.append("Multi-day journaling and mood activity available.")

    if journal_count >= 5 and mood_count >= 5 and active_days >= 4:
        level = "rich"
        confidence = "high"
        reasons.append("Strong cross-feature weekly signal available.")

    return {
        "level": level,
        "confidence": confidence,
        "reasons": reasons,
    }


def detect_contradictions(context: dict[str, Any]) -> bool:
    """
    Very simple first-pass contradiction detection.
    """
    tone_distribution = context["journal"].get("tone_distribution", {})
    mood_variance = context["mood"].get("variance") or 0
    mood_trend = context["mood"].get("trend")

    positive_count = tone_distribution.get("positive", 0)
    negative_count = tone_distribution.get("negative", 0)

    mixed_journal_tone = positive_count > 0 and negative_count > 0
    volatile_mood = mood_variance >= 2.5
    unstable_direction = mood_trend == "mixed"

    return mixed_journal_tone or volatile_mood or unstable_direction


def build_cross_signal_patterns(context: dict[str, Any]) -> list[str]:
    """
    Rule-based observations. These complement the AI output and can also be
    shown even when the AI is skipped.
    """
    patterns: list[str] = []

    mood_avg = context["mood"].get("avg_score")
    mood_trend = context["mood"].get("trend")
    habit_rate = context["habits"].get("completion_rate")
    gratitude_count = context["journal"].get("types", {}).get("gratitude", 0)
    reflection_count = context["journal"].get("types", {}).get("reflection", 0)
    distortions = context["journal"].get("distortions", {})
    procrastination_total = context["procrastination"].get("tasks", 0)
    procrastination_completed = context["procrastination"].get("completed", 0)

    if mood_avg is not None and habit_rate is not None:
        if mood_avg >= 7 and habit_rate >= 0.6:
            patterns.append("Higher mood and stronger habit follow-through appeared together this week.")
        elif mood_avg <= 5 and habit_rate < 0.4:
            patterns.append("Lower mood and weaker habit consistency appeared in the same week.")

    if gratitude_count >= 2 and mood_avg is not None and mood_avg >= 6:
        patterns.append("Gratitude journaling showed up during relatively steadier mood periods.")

    if reflection_count >= 2 and distortions:
        patterns.append("Reflection entries surfaced recurring thinking patterns worth watching over time.")

    if procrastination_total > 0:
        completion_rate = procrastination_completed / procrastination_total
        if completion_rate < 0.5:
            patterns.append("Task follow-through in the procrastination tracker felt uneven this week.")
        elif completion_rate >= 0.75:
            patterns.append("Task follow-through was relatively steady in the procrastination tracker.")

    if mood_trend == "upward":
        patterns.append("Mood scores trended upward across the week.")
    elif mood_trend == "downward":
        patterns.append("Mood scores trended downward across the week.")

    return dedupe_preserve_order(patterns)


def save_insufficient_insight(
    user_id: int,
    week_start: date,
    week_end: date,
    context: dict[str, Any],
    contradiction_flag: bool,
    sufficiency: dict[str, Any],
) -> WeeklyInsight:
    """
    Save a non-generated weekly insight so the page still has a consistent record.
    """
    insight = WeeklyInsight(
        user_id=user_id,
        week_start=week_start,
        week_end=week_end,
        summary=None,
        patterns=[],
        contradictions=None,
        suggestions=[],
        sufficiency_level=sufficiency["level"],
        confidence_level=sufficiency["confidence"],
        contradiction_flag=contradiction_flag,
        signals_used=build_signals_used(context),
        structured_context=context,
        generated_at=None,
    )
    db.session.add(insight)
    db.session.commit()
    return insight


def save_generated_insight(
    user_id: int,
    week_start: date,
    week_end: date,
    context: dict[str, Any],
    sufficiency: dict[str, Any],
    contradiction_flag: bool,
    cross_signal_patterns: list[str],
    ai_output: dict[str, Any],
) -> WeeklyInsight:
    """
    Save the AI-generated weekly insight.
    """
    merged_patterns = dedupe_preserve_order(
        (ai_output.get("patterns") or []) + cross_signal_patterns
    )

    insight = WeeklyInsight(
        user_id=user_id,
        week_start=week_start,
        week_end=week_end,
        summary=ai_output.get("summary"),
        patterns=merged_patterns,
        contradictions=ai_output.get("contradictions"),
        suggestions=ai_output.get("suggestions") or [],
        sufficiency_level=sufficiency["level"],
        confidence_level=sufficiency["confidence"],
        contradiction_flag=contradiction_flag,
        signals_used=build_signals_used(context),
        structured_context=context,
        generated_at=datetime.utcnow(),
    )
    db.session.add(insight)
    db.session.commit()
    return insight


def build_insight_response(insight: WeeklyInsight) -> dict[str, Any]:
    """
    Normalize DB row into template-friendly payload.
    """
    return {
        "id": insight.id,
        "week_start": insight.week_start,
        "week_end": insight.week_end,
        "summary": insight.summary,
        "patterns": insight.patterns or [],
        "contradictions": insight.contradictions,
        "suggestions": insight.suggestions or [],
        "sufficiency_level": insight.sufficiency_level,
        "confidence_level": insight.confidence_level,
        "contradiction_flag": insight.contradiction_flag,
        "signals_used": insight.signals_used or {},
        "structured_context": insight.structured_context or {},
        "generated_at": insight.generated_at,
    }


# ---------------------------------------------------------------------------
# Aggregation helpers
# Replace placeholder queries with your real models/fields.
# ---------------------------------------------------------------------------

def aggregate_journal_data(user_id: int, week_start: date, week_end: date) -> dict[str, Any]:
    """
    Replace with your real journal query logic.

    Expected output fields:
    - count
    - types
    - avg_length
    - tone_distribution
    - distortions
    - top_keywords
    - entry_dates
    """
    entries = []  # Replace with JournalEntry query

    type_counts: dict[str, int] = {
        "simple": 0,
        "gratitude": 0,
        "reflection": 0,
    }
    tone_distribution: dict[str, int] = defaultdict(int)
    distortions: dict[str, int] = defaultdict(int)
    keywords: list[str] = []
    word_counts: list[int] = []
    entry_dates: set[str] = set()

    for entry in entries:
        entry_type = getattr(entry, "entry_type", "simple") or "simple"
        type_counts[entry_type] = type_counts.get(entry_type, 0) + 1

        content = (getattr(entry, "content", "") or "").strip()
        if content:
            keywords.extend(extract_simple_keywords(content))
            word_counts.append(len(content.split()))

        created_at = getattr(entry, "created_at", None)
        if created_at:
            entry_dates.add(created_at.date().isoformat())

        # Replace with your actual analysis access pattern
        analysis = getattr(entry, "analysis", None)
        if analysis:
            tone = getattr(analysis, "tone", None)
            if tone:
                tone_distribution[tone] += 1

            distortion_list = getattr(analysis, "distortions", None) or []
            for distortion in distortion_list:
                distortions[distortion] += 1

    return {
        "count": len(entries),
        "types": type_counts,
        "avg_length": round(mean(word_counts), 1) if word_counts else 0,
        "tone_distribution": dict(tone_distribution),
        "distortions": dict(distortions),
        "top_keywords": get_top_items(keywords, limit=8),
        "entry_dates": entry_dates,
    }


def aggregate_mood_data(user_id: int, week_start: date, week_end: date) -> dict[str, Any]:
    """
    Replace with your real mood query logic.
    """
    mood_entries = []  # Replace with MoodEntry query

    scores: list[float] = []
    entry_dates: set[str] = set()

    for mood_entry in mood_entries:
        score = getattr(mood_entry, "score", None)
        if score is not None:
            scores.append(float(score))

        created_at = getattr(mood_entry, "created_at", None)
        if created_at:
            entry_dates.add(created_at.date().isoformat())

    return {
        "entries": len(mood_entries),
        "avg_score": round(mean(scores), 2) if scores else None,
        "variance": calculate_variance(scores) if len(scores) > 1 else 0,
        "min_score": min(scores) if scores else None,
        "max_score": max(scores) if scores else None,
        "trend": determine_mood_trend(scores),
        "entry_dates": entry_dates,
    }


def aggregate_habit_data(user_id: int, week_start: date, week_end: date) -> dict[str, Any]:
    """
    Replace with your real habit and habit log query logic.
    """
    active_habits = []  # Replace with Habit query
    completed_logs = []  # Replace with HabitLog query

    log_dates: set[str] = set()

    for log in completed_logs:
        completed_at = getattr(log, "completed_at", None) or getattr(log, "created_at", None)
        if completed_at:
            log_dates.add(completed_at.date().isoformat())

    expected_logs = len(active_habits) * 7 if active_habits else 0
    completion_rate = round(len(completed_logs) / expected_logs, 2) if expected_logs > 0 else 0

    return {
        "active": len(active_habits),
        "completed_logs": len(completed_logs),
        "completion_rate": completion_rate,
        "log_dates": log_dates,
    }


def aggregate_procrastination_data(user_id: int, week_start: date, week_end: date) -> dict[str, Any]:
    """
    Replace with your real procrastination task query logic.
    """
    tasks = []  # Replace with ProcrastinationTask query

    completed_count = 0
    task_dates: set[str] = set()

    for task in tasks:
        if getattr(task, "is_completed", False):
            completed_count += 1

        task_date = getattr(task, "created_at", None)
        if task_date:
            task_dates.add(task_date.date().isoformat())

    completion_rate = round(completed_count / len(tasks), 2) if tasks else 0

    return {
        "tasks": len(tasks),
        "completed": completed_count,
        "completion_rate": completion_rate,
        "task_dates": task_dates,
    }


# ---------------------------------------------------------------------------
# AI integration
# Replace the stub with your real OpenAI call later.
# ---------------------------------------------------------------------------

def generate_ai_weekly_insight(
    context: dict[str, Any],
    sufficiency: dict[str, Any],
    contradiction_flag: bool,
    cross_signal_patterns: list[str],
) -> dict[str, Any]:
    """
    Placeholder AI generator.

    Replace with your real OpenAI integration later.
    """
    summary = build_fallback_summary(context, contradiction_flag)

    contradictions = None
    if contradiction_flag:
        contradictions = (
            "Some signals this week appear mixed, so the overall picture may be better "
            "read as a changing or uneven week rather than one clear pattern."
        )

    suggestions = build_gentle_suggestions(context)

    return {
        "summary": summary,
        "patterns": cross_signal_patterns,
        "contradictions": contradictions,
        "suggestions": suggestions,
    }


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def calculate_active_days(
    journal_dates: set[str],
    mood_dates: set[str],
    habit_dates: set[str],
    procrastination_dates: set[str],
) -> int:
    all_dates = set()
    all_dates.update(journal_dates)
    all_dates.update(mood_dates)
    all_dates.update(habit_dates)
    all_dates.update(procrastination_dates)
    return len(all_dates)


def build_signals_used(context: dict[str, Any]) -> dict[str, int]:
    return {
        "journal_count": context["journal"]["count"],
        "mood_entries": context["mood"]["entries"],
        "habit_active": context["habits"]["active"],
        "habit_completed_logs": context["habits"]["completed_logs"],
        "procrastination_tasks": context["procrastination"]["tasks"],
        "procrastination_completed": context["procrastination"]["completed"],
        "active_days": context["activity"]["active_days"],
    }


def extract_simple_keywords(text: str) -> list[str]:
    if not text:
        return []

    stop_words = {
        "the", "and", "is", "in", "it", "to", "of", "a", "i", "was", "for", "on",
        "that", "with", "my", "this", "had", "are", "but", "have", "just", "been",
        "from", "they", "them", "then", "into", "about", "your", "their", "felt",
    }

    cleaned_words = []
    for raw_word in text.split():
        word = raw_word.strip(".,!?;:()[]{}\"'").lower()
        if len(word) > 3 and word not in stop_words:
            cleaned_words.append(word)

    return cleaned_words


def get_top_items(items: list[str], limit: int = 8) -> list[str]:
    counter = Counter(items)
    return [item for item, _count in counter.most_common(limit)]


def calculate_variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0

    avg = sum(values) / len(values)
    variance = sum((value - avg) ** 2 for value in values) / len(values)
    return round(variance, 2)


def determine_mood_trend(scores: list[float]) -> str:
    if len(scores) < 2:
        return "insufficient"

    deltas = [scores[i] - scores[i - 1] for i in range(1, len(scores))]
    positives = sum(1 for delta in deltas if delta > 0)
    negatives = sum(1 for delta in deltas if delta < 0)

    if positives > 0 and negatives > 0:
        return "mixed"
    if scores[-1] > scores[0]:
        return "upward"
    if scores[-1] < scores[0]:
        return "downward"
    return "stable"


def build_fallback_summary(context: dict[str, Any], contradiction_flag: bool) -> str:
    journal_count = context["journal"]["count"]
    mood_count = context["mood"]["entries"]
    active_days = context["activity"]["active_days"]

    if contradiction_flag:
        return (
            f"This week includes activity across {active_days} day(s), with {journal_count} "
            f"journal entry/entries and {mood_count} mood check-in(s). The overall picture "
            f"looks somewhat mixed, so it may be more useful to treat this as an uneven week "
            f"than to force a single conclusion."
        )

    return (
        f"This week includes activity across {active_days} day(s), with {journal_count} "
        f"journal entry/entries and {mood_count} mood check-in(s). There appears to be enough "
        f"signal for a light weekly reflection, while some patterns may still become clearer "
        f"with continued use over time."
    )


def build_gentle_suggestions(context: dict[str, Any]) -> list[str]:
    suggestions: list[str] = []

    if context["journal"]["count"] < 3:
        suggestions.append("A few more journal entries across different days may help patterns become clearer.")

    if context["mood"]["entries"] < 4:
        suggestions.append("More regular mood check-ins could make weekly shifts easier to understand.")

    if context["habits"]["completion_rate"] < 0.4 and context["habits"]["active"] > 0:
        suggestions.append("It may help to notice whether low-follow-through days line up with lower-energy days.")

    if context["journal"]["types"].get("gratitude", 0) == 0:
        suggestions.append("Trying a gratitude entry once or twice may add another useful perspective to the week.")

    return dedupe_preserve_order(suggestions)[:3]


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen = set()
    deduped: list[str] = []

    for item in items:
        if item and item not in seen:
            seen.add(item)
            deduped.append(item)

    return deduped