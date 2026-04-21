from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from statistics import mean
from typing import Any, Optional
from zoneinfo import ZoneInfo

from app.extensions import db
from app.models.habit import Habit
from app.models.habit_log import HabitLog
from app.models.journal import JournalEntry
from app.models.mood_checklist import MoodChecklistResult
from app.models.procrastination_sheet import ProcrastinationSheet
from app.models.weekly_insight import WeeklyInsight
from app.services.weekly_insight_service import generate_weekly_insight_payload


# ---------------------------------------------------------------------------
# Timezone helpers
# ---------------------------------------------------------------------------

def get_user_timezone(user) -> ZoneInfo:
    """
    Return the user's timezone.

    Falls back to UTC when the user has no timezone stored.
    """
    timezone_name = getattr(user, "timezone", None) or "UTC"
    return ZoneInfo(timezone_name)


def get_week_range_for_user(
    user,
    target_date: Optional[date] = None,
) -> tuple[date, date]:
    """
    Return the Monday-Sunday week range for the user in their local timezone.

    If target_date is provided, it is treated as already representing the
    relevant local date.
    """
    user_timezone = get_user_timezone(user)

    if target_date is None:
        local_today = datetime.now(user_timezone).date()
    else:
        local_today = target_date

    week_start = local_today - timedelta(days=local_today.weekday())
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def get_week_datetime_range_for_user(
    week_start: date,
    week_end: date,
    user_timezone: ZoneInfo,
) -> tuple[datetime, datetime]:
    """
    Build an inclusive-exclusive datetime range for the user's local week.

    The returned datetimes are converted to UTC so they can be safely used
    against timezone-aware timestamps stored in the database.
    """
    local_start = datetime.combine(week_start, time.min, tzinfo=user_timezone)
    local_end = datetime.combine(
        week_end + timedelta(days=1),
        time.min,
        tzinfo=user_timezone,
    )

    utc_start = local_start.astimezone(timezone.utc)
    utc_end = local_end.astimezone(timezone.utc)

    return utc_start, utc_end


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def get_or_generate_weekly_insight(
    user,
    target_date: Optional[date] = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """
    Return the weekly insight payload for a user, generating and saving it if needed.

    Flow:
    1. Resolve the user's local week range
    2. Return cached insight if it exists and refresh is not forced
    3. Build structured weekly context
    4. Evaluate sufficiency + contradictions + cross-signal patterns
    5. Save a restrained fallback insight if signal is insufficient
    6. Otherwise call the weekly insight service and save the generated insight
    7. Return a normalized response for route/template use
    """
    week_start, week_end = get_week_range_for_user(user, target_date)

    existing_insight = WeeklyInsight.query.filter_by(
        user_id=user.id,
        week_start=week_start,
    ).first()

    if existing_insight and not force_refresh:
        return build_insight_response(existing_insight)

    if existing_insight and force_refresh:
        db.session.delete(existing_insight)
        db.session.commit()

    context = build_weekly_context(
        user=user,
        week_start=week_start,
        week_end=week_end,
    )

    sufficiency = check_insight_sufficiency(context)
    contradiction_flag = detect_contradictions(context)
    cross_signal_patterns = build_cross_signal_patterns(context)

    if sufficiency["level"] == "insufficient":
        saved_insight = save_insufficient_insight(
            user=user,
            week_start=week_start,
            week_end=week_end,
            context=context,
            contradiction_flag=contradiction_flag,
            sufficiency=sufficiency,
            cross_signal_patterns=cross_signal_patterns,
        )
        return build_insight_response(saved_insight)

    ai_output = generate_weekly_insight_payload(
        context=context,
        sufficiency=sufficiency,
        contradiction_flag=contradiction_flag,
        cross_signal_patterns=cross_signal_patterns,
    )

    saved_insight = save_generated_insight(
        user=user,
        week_start=week_start,
        week_end=week_end,
        context=context,
        sufficiency=sufficiency,
        contradiction_flag=contradiction_flag,
        cross_signal_patterns=cross_signal_patterns,
        ai_output=ai_output,
    )

    return build_insight_response(saved_insight)


# ---------------------------------------------------------------------------
# Weekly context construction
# ---------------------------------------------------------------------------

def build_weekly_context(
    user,
    week_start: date,
    week_end: date,
) -> dict[str, Any]:
    """
    Build the structured weekly context used by both the UI and the AI service.

    This context intentionally focuses on behavioral signals rather than any
    personal identity or speculative life context.
    """
    journal_data = aggregate_journal_data(user, week_start, week_end)
    mood_data = aggregate_mood_data(user, week_start, week_end)
    habits_data = aggregate_habit_data(user, week_start, week_end)
    procrastination_data = aggregate_procrastination_data(user, week_start, week_end)

    active_days = calculate_active_days(
        journal_dates=journal_data["entry_dates"],
        mood_dates=mood_data["entry_dates"],
        habit_dates=habits_data["log_dates"],
        procrastination_dates=procrastination_data["sheet_dates"],
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
            "sheets": procrastination_data["sheets"],
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
    Evaluate whether the current week has enough signal for a meaningful reflection.

    UI-facing levels:
    - insufficient
    - building
    - strong

    Internal confidence stays:
    - low
    - medium
    - high
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
        level = "building"
        confidence = "low"
        reasons.append("Minimum weekly activity threshold met.")

    if journal_count >= 4 and mood_count >= 4 and active_days >= 3:
        level = "building"
        confidence = "medium"
        reasons.append("Multi-day journaling and mood activity available.")

    if journal_count >= 5 and mood_count >= 5 and active_days >= 4:
        level = "strong"
        confidence = "high"
        reasons.append("Strong cross-feature weekly signal available.")

    return {
        "level": level,
        "confidence": confidence,
        "reasons": reasons,
        "label": get_signal_strength_label(level),
        "confidence_note": build_confidence_note(level, confidence),
    }


def detect_contradictions(context: dict[str, Any]) -> bool:
    """
    Detect whether the week's signals look mixed or internally inconsistent.

    This is intentionally light-touch and should only flag visible signal tension,
    not infer any deeper psychological conclusion.
    """
    tone_distribution = context["journal"].get("tone_distribution", {})
    mood_variance = context["mood"].get("variance") or 0
    mood_trend = context["mood"].get("trend")
    gratitude_count = context["journal"].get("types", {}).get("gratitude", 0)

    positive_count = tone_distribution.get("positive", 0)
    negative_count = tone_distribution.get("negative", 0)

    mixed_journal_tone = positive_count > 0 and negative_count > 0
    volatile_mood = mood_variance >= 3
    mixed_mood_direction = mood_trend == "mixed"
    gratitude_with_negative_tone = gratitude_count > 0 and negative_count > 0

    return any(
        [
            mixed_journal_tone,
            volatile_mood,
            mixed_mood_direction,
            gratitude_with_negative_tone,
        ]
    )


def build_cross_signal_patterns(context: dict[str, Any]) -> list[str]:
    """
    Build lightweight cross-feature observations directly from structured data.

    These are deterministic observations from the backend and can be merged with
    AI-generated observations later.
    """
    patterns: list[str] = []

    mood_avg = context["mood"].get("avg_score")
    mood_trend = context["mood"].get("trend")
    gratitude_count = context["journal"].get("types", {}).get("gratitude", 0)
    reflection_count = context["journal"].get("types", {}).get("reflection", 0)
    distortions = context["journal"].get("distortions", {})
    journal_count = context["journal"].get("count", 0)
    habit_rate = context["habits"].get("completion_rate")
    procrastination_rate = context["procrastination"].get("completion_rate")

    if journal_count >= 3 and mood_trend == "upward":
        patterns.append(
            "Mood scores improved alongside regular journaling activity this week."
        )

    if gratitude_count >= 2 and mood_avg is not None and mood_avg >= 6:
        patterns.append(
            "Gratitude entries appeared during relatively steadier mood periods."
        )

    if reflection_count >= 2 and distortions:
        patterns.append(
            "Reflection entries surfaced recurring thinking patterns worth noticing over time."
        )

    if mood_trend == "downward" and journal_count >= 2:
        patterns.append(
            "Mood dipped across the week while journaling continued, which suggests a mixed week rather than one clear pattern."
        )

    if habit_rate is not None and mood_avg is not None:
        if habit_rate >= 0.6 and mood_avg >= 7:
            patterns.append(
                "Higher mood and stronger habit consistency appeared together this week."
            )
        elif habit_rate < 0.4 and mood_avg <= 5:
            patterns.append(
                "Lower mood and weaker habit consistency appeared in the same week."
            )

    if procrastination_rate is not None and procrastination_rate < 0.5:
        patterns.append(
            "Follow-through in the procrastination tool felt uneven this week."
        )

    return dedupe_preserve_order(patterns)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def save_insufficient_insight(
    user,
    week_start: date,
    week_end: date,
    context: dict[str, Any],
    contradiction_flag: bool,
    sufficiency: dict[str, Any],
    cross_signal_patterns: list[str],
) -> WeeklyInsight:
    """
    Save a restrained weekly insight for low-signal weeks.

    Even when signal is insufficient, the saved record still includes enough
    structured UI metadata for the page to render consistently.
    """
    fallback_payload = build_insufficient_payload(
        context=context,
        sufficiency=sufficiency,
        contradiction_flag=contradiction_flag,
        cross_signal_patterns=cross_signal_patterns,
    )

    enriched_context = build_enriched_context(
        base_context=context,
        insight_meta=fallback_payload["insight_meta"],
    )

    insight = WeeklyInsight(
        user_id=user.id,
        week_start=week_start,
        week_end=week_end,
        summary=fallback_payload["summary"],
        patterns=fallback_payload["patterns"],
        contradictions=fallback_payload["contradictions"],
        suggestions=fallback_payload["suggestions"],
        sufficiency_level=sufficiency["level"],
        confidence_level=sufficiency["confidence"],
        contradiction_flag=contradiction_flag,
        signals_used=build_signals_used(context),
        structured_context=enriched_context,
        generated_at=None,
    )
    db.session.add(insight)
    db.session.commit()
    return insight


def save_generated_insight(
    user,
    week_start: date,
    week_end: date,
    context: dict[str, Any],
    sufficiency: dict[str, Any],
    contradiction_flag: bool,
    cross_signal_patterns: list[str],
    ai_output: dict[str, Any],
) -> WeeklyInsight:
    """
    Save a generated weekly insight using the current WeeklyInsight model.

    The main hero reflection is stored in `summary`, cross-signal observations
    in `patterns`, and small extra UI metadata is stored under
    `structured_context["insight_meta"]`.
    """
    merged_patterns = dedupe_preserve_order(
        (ai_output.get("cross_signal_observations") or [])
        + cross_signal_patterns
    )

    contradictions = ai_output.get("contradictions")
    if contradiction_flag and not contradictions:
        contradictions = (
            "Some signals this week appear mixed, so the overall picture may be better "
            "read as a changing or uneven week rather than one clear pattern."
        )

    insight_meta = {
        "emotional_trend": ai_output.get("emotional_trend"),
        "confidence_note": ai_output.get("confidence_note") or sufficiency["confidence_note"],
        "signal_strength_label": ai_output.get("signal_strength_label") or sufficiency["label"],
    }

    enriched_context = build_enriched_context(
        base_context=context,
        insight_meta=insight_meta,
    )

    insight = WeeklyInsight(
        user_id=user.id,
        week_start=week_start,
        week_end=week_end,
        summary=ai_output.get("hero_summary"),
        patterns=merged_patterns,
        contradictions=contradictions,
        suggestions=ai_output.get("suggestions") or [],
        sufficiency_level=sufficiency["level"],
        confidence_level=sufficiency["confidence"],
        contradiction_flag=contradiction_flag,
        signals_used=build_signals_used(context),
        structured_context=enriched_context,
        generated_at=datetime.now(timezone.utc),
    )
    db.session.add(insight)
    db.session.commit()
    return insight


def build_insight_response(insight: WeeklyInsight) -> dict[str, Any]:
    """
    Normalize a WeeklyInsight record into a template-friendly payload.

    This lets the route and template stay simple even when the database schema
    is still using broad fields like summary/patterns/suggestions.
    """
    structured_context = insight.structured_context or {}
    insight_meta = structured_context.get("insight_meta", {})

    summary = insight.summary
    if not summary and insight.sufficiency_level == "insufficient":
        summary = (
            "There is not enough activity this week to generate a meaningful reflection yet. "
            "More entries across different days can help create a clearer picture over time."
        )

    return {
        "id": insight.id,
        "week_start": insight.week_start,
        "week_end": insight.week_end,
        "summary": summary,
        "hero_summary": summary,
        "emotional_trend": insight_meta.get("emotional_trend"),
        "patterns": insight.patterns or [],
        "contradictions": insight.contradictions,
        "suggestions": insight.suggestions or [],
        "sufficiency_level": insight.sufficiency_level,
        "confidence_level": insight.confidence_level,
        "contradiction_flag": insight.contradiction_flag,
        "signal_strength_label": insight_meta.get(
            "signal_strength_label",
            get_signal_strength_label(insight.sufficiency_level),
        ),
        "confidence_note": insight_meta.get(
            "confidence_note",
            build_confidence_note(insight.sufficiency_level, insight.confidence_level),
        ),
        "signals_used": insight.signals_used or {},
        "structured_context": structured_context,
        "generated_at": insight.generated_at,
    }


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def aggregate_journal_data(
    user,
    week_start: date,
    week_end: date,
) -> dict[str, Any]:
    """
    Aggregate journal activity for the target week.

    This gathers weekly entry counts, entry mix, recurring keywords, tone
    distribution, and detected cognitive distortion counts.
    """
    user_timezone = get_user_timezone(user)
    start_dt, end_dt = get_week_datetime_range_for_user(
        week_start,
        week_end,
        user_timezone,
    )

    entries = (
        JournalEntry.query
        .filter(
            JournalEntry.user_id == user.id,
            JournalEntry.created_at >= start_dt,
            JournalEntry.created_at < end_dt,
        )
        .order_by(JournalEntry.created_at.asc())
        .all()
    )

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
        entry_type = (getattr(entry, "entry_type", "simple") or "simple").strip().lower()
        type_counts[entry_type] = type_counts.get(entry_type, 0) + 1

        content = (getattr(entry, "content", "") or "").strip()
        if content:
            keywords.extend(extract_simple_keywords(content))
            word_counts.append(len(content.split()))

        if entry.created_at:
            entry_dates.add(entry.created_at.date().isoformat())

        tone = getattr(entry, "tone", None)
        if tone:
            tone_distribution[str(tone).strip().lower()] += 1

        distortion_list = getattr(entry, "cognitive_distortions", None) or []
        for distortion in distortion_list:
            distortions[str(distortion).strip().lower()] += 1

    return {
        "count": len(entries),
        "types": type_counts,
        "avg_length": round(mean(word_counts), 1) if word_counts else 0,
        "tone_distribution": dict(tone_distribution),
        "distortions": dict(distortions),
        "top_keywords": get_top_items(keywords, limit=8),
        "entry_dates": entry_dates,
    }


def aggregate_mood_data(
    user,
    week_start: date,
    week_end: date,
) -> dict[str, Any]:
    """
    Aggregate mood checklist activity for the target week.
    """
    user_timezone = get_user_timezone(user)
    start_dt, end_dt = get_week_datetime_range_for_user(
        week_start,
        week_end,
        user_timezone,
    )

    mood_entries = (
        MoodChecklistResult.query
        .filter(
            MoodChecklistResult.user_id == user.id,
            MoodChecklistResult.created_at >= start_dt,
            MoodChecklistResult.created_at < end_dt,
        )
        .order_by(MoodChecklistResult.created_at.asc())
        .all()
    )

    scores: list[float] = []
    entry_dates: set[str] = set()

    for mood_entry in mood_entries:
        score = getattr(mood_entry, "total_score", None)
        if score is not None:
            scores.append(float(score))

        if mood_entry.created_at:
            entry_dates.add(mood_entry.created_at.date().isoformat())

    return {
        "entries": len(mood_entries),
        "avg_score": round(mean(scores), 2) if scores else None,
        "variance": calculate_variance(scores) if len(scores) > 1 else 0,
        "min_score": min(scores) if scores else None,
        "max_score": max(scores) if scores else None,
        "trend": determine_mood_trend(scores),
        "entry_dates": entry_dates,
    }


def aggregate_habit_data(
    user,
    week_start: date,
    week_end: date,
) -> dict[str, Any]:
    """
    Aggregate habit activity for the target week.

    Completion rate is calculated as completed logs divided by expected logs
    for all active habits across seven days.
    """
    user_timezone = get_user_timezone(user)
    start_dt, end_dt = get_week_datetime_range_for_user(
        week_start,
        week_end,
        user_timezone,
    )

    active_habits = (
        Habit.query
        .filter(
            Habit.user_id == user.id,
            getattr(Habit, "is_archived", False) == False if hasattr(Habit, "is_archived") else True,
        )
        .all()
    )

    active_habit_ids = [habit.id for habit in active_habits]

    if active_habit_ids:
        completed_logs = (
            HabitLog.query
            .filter(
                HabitLog.habit_id.in_(active_habit_ids),
                HabitLog.created_at >= start_dt,
                HabitLog.created_at < end_dt,
            )
            .all()
        )
    else:
        completed_logs = []

    log_dates: set[str] = set()

    for log in completed_logs:
        log_dt = getattr(log, "completed_at", None) or getattr(log, "created_at", None)
        if log_dt:
            log_dates.add(log_dt.date().isoformat())

    expected_logs = len(active_habits) * 7 if active_habits else 0
    completion_rate = round(len(completed_logs) / expected_logs, 2) if expected_logs > 0 else 0

    return {
        "active": len(active_habits),
        "completed_logs": len(completed_logs),
        "completion_rate": completion_rate,
        "log_dates": log_dates,
    }


def aggregate_procrastination_data(
    user,
    week_start: date,
    week_end: date,
) -> dict[str, Any]:
    """
    Aggregate procrastination sheet activity for the target week.
    """
    user_timezone = get_user_timezone(user)
    start_dt, end_dt = get_week_datetime_range_for_user(
        week_start,
        week_end,
        user_timezone,
    )

    sheets = (
        ProcrastinationSheet.query
        .filter(
            ProcrastinationSheet.user_id == user.id,
            ProcrastinationSheet.created_at >= start_dt,
            ProcrastinationSheet.created_at < end_dt,
        )
        .order_by(ProcrastinationSheet.created_at.asc())
        .all()
    )

    completed_count = 0
    sheet_dates: set[str] = set()

    for sheet in sheets:
        if getattr(sheet, "is_completed", False):
            completed_count += 1

        if sheet.created_at:
            sheet_dates.add(sheet.created_at.date().isoformat())

    completion_rate = round(completed_count / len(sheets), 2) if sheets else 0

    return {
        "sheets": len(sheets),
        "completed": completed_count,
        "completion_rate": completion_rate,
        "sheet_dates": sheet_dates,
    }


# ---------------------------------------------------------------------------
# Fallback builders
# ---------------------------------------------------------------------------

def build_insufficient_payload(
    context: dict[str, Any],
    sufficiency: dict[str, Any],
    contradiction_flag: bool,
    cross_signal_patterns: list[str],
) -> dict[str, Any]:
    """
    Build a restrained fallback payload for weeks with insufficient activity.

    This keeps the UI consistent without overstating weak signals.
    """
    contradictions = None
    if contradiction_flag:
        contradictions = (
            "Some signals this week appear mixed, so the overall picture may be better "
            "read as a changing or uneven week rather than one clear pattern."
        )

    return {
        "summary": (
            "There is not enough activity this week to generate a strong reflection yet. "
            "A few more entries across different days can help the picture become clearer."
        ),
        "patterns": cross_signal_patterns[:2],
        "contradictions": contradictions,
        "suggestions": build_gentle_suggestions(context),
        "insight_meta": {
            "emotional_trend": (
                "There is not enough mood and journaling activity yet to describe a clear weekly emotional trend."
            ),
            "confidence_note": sufficiency["confidence_note"],
            "signal_strength_label": sufficiency["label"],
        },
    }


def build_gentle_suggestions(context: dict[str, Any]) -> list[str]:
    """
    Build small non-intrusive suggestions from weekly behavior patterns.

    Suggestions stay practical, neutral, and directly tied to the observed
    weekly signals.
    """
    suggestions: list[str] = []

    if context["journal"]["count"] < 3:
        suggestions.append(
            "A few more journal entries across different days may help patterns become clearer."
        )

    if context["mood"]["entries"] < 4:
        suggestions.append(
            "More regular mood check-ins could make weekly shifts easier to understand."
        )

    if context["habits"]["completion_rate"] < 0.4 and context["habits"]["active"] > 0:
        suggestions.append(
            "It may help to notice whether lower-follow-through days line up with lower-energy days."
        )

    if context["journal"]["types"].get("gratitude", 0) == 0:
        suggestions.append(
            "Trying a gratitude entry once or twice may add another useful perspective to the week."
        )

    return dedupe_preserve_order(suggestions)[:3]


def build_enriched_context(
    base_context: dict[str, Any],
    insight_meta: dict[str, Any],
) -> dict[str, Any]:
    """
    Attach UI-friendly insight metadata to the structured context.

    This avoids requiring an immediate database migration while still giving
    the template richer fields to render.
    """
    enriched_context = dict(base_context)
    enriched_context["insight_meta"] = insight_meta
    return enriched_context


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def calculate_active_days(
    journal_dates: set[str],
    mood_dates: set[str],
    habit_dates: set[str],
    procrastination_dates: set[str],
) -> int:
    """
    Count unique active days across all supported weekly signals.
    """
    all_dates = set()
    all_dates.update(journal_dates)
    all_dates.update(mood_dates)
    all_dates.update(habit_dates)
    all_dates.update(procrastination_dates)
    return len(all_dates)


def build_signals_used(context: dict[str, Any]) -> dict[str, int]:
    """
    Build a compact summary of the weekly signals used for the insight.
    """
    return {
        "journal_count": context["journal"]["count"],
        "mood_entries": context["mood"]["entries"],
        "habit_active": context["habits"]["active"],
        "habit_completed_logs": context["habits"]["completed_logs"],
        "procrastination_sheets": context["procrastination"]["sheets"],
        "procrastination_completed": context["procrastination"]["completed"],
        "active_days": context["activity"]["active_days"],
    }


def extract_simple_keywords(text: str) -> list[str]:
    """
    Extract simple recurring keywords from journal content.

    This intentionally stays lightweight and avoids sending raw personal text
    into the weekly signal summary.
    """
    if not text:
        return []

    stop_words = {
        "the", "and", "is", "in", "it", "to", "of", "a", "i", "was",
        "for", "on", "that", "with", "my", "this", "had", "are", "but",
        "have", "just", "been", "from", "they", "them", "then", "into",
        "about", "your", "their", "felt",
    }

    cleaned_words = []
    for raw_word in text.split():
        word = raw_word.strip(".,!?;:()[]{}\"'").lower()
        if len(word) > 3 and word not in stop_words:
            cleaned_words.append(word)

    return cleaned_words


def get_top_items(items: list[str], limit: int = 8) -> list[str]:
    """
    Return the most common items while preserving only the item values.
    """
    counter = Counter(items)
    return [item for item, _count in counter.most_common(limit)]


def calculate_variance(values: list[float]) -> float:
    """
    Calculate simple population variance for a list of numeric values.
    """
    if len(values) < 2:
        return 0

    avg = sum(values) / len(values)
    variance = sum((value - avg) ** 2 for value in values) / len(values)
    return round(variance, 2)


def determine_mood_trend(scores: list[float]) -> str:
    """
    Classify mood direction across the week using the first and last score.
    """
    if len(scores) < 2:
        return "insufficient"

    first_score = scores[0]
    last_score = scores[-1]
    delta = last_score - first_score

    if abs(delta) < 0.5:
        return "stable"
    if delta >= 0.5:
        return "upward"
    if delta <= -0.5:
        return "downward"
    return "mixed"


def get_signal_strength_label(level: str) -> str:
    """
    Convert a sufficiency level into cleaner UI text.
    """
    if level == "strong":
        return "Strong signal"
    if level == "building":
        return "Building signal"
    return "Limited signal"


def build_confidence_note(level: str, confidence: str) -> str:
    """
    Build a small confidence note for UI display.
    """
    if level == "strong":
        return "Multiple activity signals aligned this week."

    if level == "building" and confidence == "medium":
        return "Patterns are emerging across multiple days."

    if level == "building":
        return "Some weekly patterns are starting to form."

    return "This reflection is based on limited weekly activity."


def dedupe_preserve_order(items: list[str]) -> list[str]:
    """
    Remove duplicates from a list while preserving original order.
    """
    seen = set()
    deduped: list[str] = []

    for item in items:
        if item and item not in seen:
            seen.add(item)
            deduped.append(item)

    return deduped