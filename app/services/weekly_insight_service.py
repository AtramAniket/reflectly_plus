from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

client = OpenAI()


def generate_weekly_insight_payload(
    context: dict[str, Any],
    sufficiency: dict[str, Any],
    contradiction_flag: bool,
    cross_signal_patterns: list[str],
) -> dict[str, Any]:
    """
    Generate a structured weekly insight payload using OpenAI.

    This service is intentionally limited to behavior-based reflection.
    It must not infer personal identity, background, or speculative life context.
    The output is designed to plug directly into the WeeklyInsight helper layer.

    Returns a normalized dictionary with:
    - hero_summary
    - emotional_trend
    - cross_signal_observations
    - suggestions
    - contradictions
    - confidence_note
    - signal_strength_label
    """
    safe_payload = build_safe_weekly_payload(
        context=context,
        sufficiency=sufficiency,
        contradiction_flag=contradiction_flag,
        cross_signal_patterns=cross_signal_patterns,
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": build_system_prompt(),
                },
                {
                    "role": "user",
                    "content": build_user_prompt(safe_payload),
                },
            ],
        )

        content = response.choices[0].message.content or "{}"
        content = content.strip()

        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        parsed = json.loads(content)

        return normalize_weekly_ai_output(
            parsed_output=parsed,
            sufficiency=sufficiency,
            contradiction_flag=contradiction_flag,
            cross_signal_patterns=cross_signal_patterns,
        )

    except Exception as exc:
        print("Weekly Insight Service Error:", exc)

        return build_service_fallback_output(
            context=context,
            sufficiency=sufficiency,
            contradiction_flag=contradiction_flag,
            cross_signal_patterns=cross_signal_patterns,
        )


def build_system_prompt() -> str:
    """
    Return the system prompt for weekly insight generation.

    The prompt is designed to keep output:
    - concise
    - neutral
    - behavior-based
    - non-diagnostic
    - free from identity assumptions
    """
    return """
You are generating a weekly reflection summary for a journaling and self-management app.

Your job is to produce calm, concise, behavior-based reflections using only the structured weekly signals provided.

Follow these rules strictly:

1. Use only the provided data.
2. Do not infer or mention personal identity, background, nationality, ethnicity, religion, gender, profession, family situation, relationship status, or life circumstances.
3. Do not speculate about causes unless they are directly supported by the provided signals.
4. Do not diagnose, label, or make medical or mental health claims.
5. Do not moralize, shame, exaggerate, or use alarmist language.
6. Do not say you "know" the user. Frame observations carefully and neutrally.
7. If signals are limited, say so clearly and keep the reflection modest.
8. Keep the tone warm, grounded, neutral, and reflective.
9. Prefer short, useful language over poetic or overly therapeutic writing.
10. Suggestions must be gentle, practical, and directly tied to the observed signals.
11. Avoid repeating the same point across multiple fields.
12. Do not mention hidden reasoning or uncertainty analysis.

Output valid JSON only.

Return this exact JSON shape:
{
  "hero_summary": "string",
  "emotional_trend": "string",
  "cross_signal_observations": ["string", "string"],
  "suggestions": ["string", "string"],
  "contradictions": "string or null",
  "confidence_note": "string",
  "signal_strength_label": "Strong signal OR Building signal OR Limited signal"
}

Field constraints:
- hero_summary: 2 to 4 short sentences
- emotional_trend: 1 to 3 short sentences
- cross_signal_observations: 2 to 3 short items
- suggestions: 1 to 2 short items
- contradictions: null unless mixed signals are clearly present
- confidence_note: 1 short sentence
- signal_strength_label: one of exactly "Strong signal", "Building signal", or "Limited signal"

Do not include markdown.
Do not include extra keys.
""".strip()


def build_user_prompt(payload: dict[str, Any]) -> str:
    """
    Return the user prompt containing the structured weekly payload.
    """
    serialized = json.dumps(payload, ensure_ascii=False, indent=2)

    return f"""
Generate the weekly reflection JSON for this structured weekly data:

{serialized}
""".strip()


def build_safe_weekly_payload(
    context: dict[str, Any],
    sufficiency: dict[str, Any],
    contradiction_flag: bool,
    cross_signal_patterns: list[str],
) -> dict[str, Any]:
    """
    Build a constrained input payload for the model.

    Only high-level, behavior-based weekly signals are included.
    Raw journal text, personal biography, and sensitive real-world specifics
    are intentionally excluded.
    """
    return {
        "week_range": {
            "start": context.get("week_start"),
            "end": context.get("week_end"),
        },
        "signal_strength": sufficiency.get("level"),
        "signal_strength_label": sufficiency.get("label"),
        "confidence": sufficiency.get("confidence"),
        "confidence_note_hint": sufficiency.get("confidence_note"),
        "contradiction_flag": contradiction_flag,
        "journal": {
            "count": context["journal"]["count"],
            "types": context["journal"]["types"],
            "avg_length": context["journal"]["avg_length"],
            "top_keywords": context["journal"]["top_keywords"],
            "tone_distribution": context["journal"]["tone_distribution"],
            "distortions": context["journal"]["distortions"],
        },
        "mood": {
            "entries": context["mood"]["entries"],
            "avg_score": context["mood"]["avg_score"],
            "variance": context["mood"]["variance"],
            "min_score": context["mood"]["min_score"],
            "max_score": context["mood"]["max_score"],
            "trend": context["mood"]["trend"],
        },
        "habits": {
            "active": context["habits"]["active"],
            "completed_logs": context["habits"]["completed_logs"],
            "completion_rate": context["habits"]["completion_rate"],
        },
        "procrastination": {
            "sheets": context["procrastination"]["sheets"],
            "completed": context["procrastination"]["completed"],
            "completion_rate": context["procrastination"]["completion_rate"],
        },
        "activity": {
            "active_days": context["activity"]["active_days"],
            "inactive_days": context["activity"]["inactive_days"],
        },
        "existing_cross_signal_patterns": cross_signal_patterns[:3],
    }


def normalize_weekly_ai_output(
    parsed_output: dict[str, Any],
    sufficiency: dict[str, Any],
    contradiction_flag: bool,
    cross_signal_patterns: list[str],
) -> dict[str, Any]:
    """
    Normalize raw model output into a safe and predictable structure.

    This protects the app from malformed JSON, missing keys, or overly long arrays.
    """
    hero_summary = clean_text(
        parsed_output.get("hero_summary"),
        fallback=build_default_hero_summary(sufficiency),
    )

    emotional_trend = clean_text(
        parsed_output.get("emotional_trend"),
        fallback=build_default_emotional_trend(sufficiency),
    )

    model_patterns = clean_text_list(
        parsed_output.get("cross_signal_observations"),
        limit=3,
    )

    if not model_patterns:
        model_patterns = cross_signal_patterns[:3]

    suggestions = clean_text_list(
        parsed_output.get("suggestions"),
        limit=2,
    )

    contradictions = clean_nullable_text(
        parsed_output.get("contradictions"),
    )

    if contradiction_flag and not contradictions:
        contradictions = (
            "Some signals this week appear mixed, so the overall picture may be better "
            "read as a changing or uneven week rather than one clear pattern."
        )

    confidence_note = clean_text(
        parsed_output.get("confidence_note"),
        fallback=sufficiency.get("confidence_note") or "This reflection is based on the available weekly signals.",
    )

    signal_strength_label = parsed_output.get("signal_strength_label")
    if signal_strength_label not in {"Strong signal", "Building signal", "Limited signal"}:
        signal_strength_label = sufficiency.get("label") or "Building signal"

    return {
        "hero_summary": hero_summary,
        "emotional_trend": emotional_trend,
        "cross_signal_observations": model_patterns,
        "suggestions": suggestions,
        "contradictions": contradictions,
        "confidence_note": confidence_note,
        "signal_strength_label": signal_strength_label,
    }


def build_service_fallback_output(
    context: dict[str, Any],
    sufficiency: dict[str, Any],
    contradiction_flag: bool,
    cross_signal_patterns: list[str],
) -> dict[str, Any]:
    """
    Build a deterministic fallback output when the OpenAI call fails.

    This keeps the page usable and avoids blocking the weekly insight flow.
    """
    contradictions = None
    if contradiction_flag:
        contradictions = (
            "Some signals this week appear mixed, so the overall picture may be better "
            "read as a changing or uneven week rather than one clear pattern."
        )

    suggestions = build_fallback_suggestions(context)

    return {
        "hero_summary": build_default_hero_summary(sufficiency),
        "emotional_trend": build_default_emotional_trend(sufficiency),
        "cross_signal_observations": cross_signal_patterns[:3],
        "suggestions": suggestions,
        "contradictions": contradictions,
        "confidence_note": sufficiency.get("confidence_note") or "This reflection is based on the available weekly signals.",
        "signal_strength_label": sufficiency.get("label") or "Building signal",
    }


def build_default_hero_summary(sufficiency: dict[str, Any]) -> str:
    """
    Build a restrained default hero summary.
    """
    level = sufficiency.get("level")

    if level == "strong":
        return (
            "This week shows enough activity to support a clearer reflection. "
            "Multiple signals suggest patterns worth paying attention to."
        )

    if level == "building":
        return (
            "This week shows some emerging patterns across your activity. "
            "The overall picture is becoming clearer, even if it is still early."
        )

    return (
        "There is not enough activity this week to support a strong reflection yet. "
        "A few more entries across different days can help the picture become clearer."
    )


def build_default_emotional_trend(sufficiency: dict[str, Any]) -> str:
    """
    Build a restrained default emotional trend line.
    """
    level = sufficiency.get("level")

    if level in {"strong", "building"}:
        return (
            "The week contains enough mood and journaling signal to suggest a developing emotional pattern, "
            "though some parts may still remain light."
        )

    return (
        "There is not enough mood and journaling activity yet to describe a clear weekly emotional trend."
    )


def build_fallback_suggestions(context: dict[str, Any]) -> list[str]:
    """
    Build safe fallback suggestions from the structured weekly context.
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

    if context["habits"]["active"] > 0 and context["habits"]["completion_rate"] < 0.4:
        suggestions.append(
            "It may help to keep routines small and manageable on lower-follow-through days."
        )

    if not suggestions:
        suggestions.append(
            "Continue using the app across multiple days to make weekly patterns easier to interpret."
        )

    return suggestions[:2]


def clean_text(value: Any, fallback: str) -> str:
    """
    Normalize a required text field.
    """
    if isinstance(value, str):
        cleaned = " ".join(value.split()).strip()
        if cleaned:
            return cleaned

    return fallback


def clean_nullable_text(value: Any) -> str | None:
    """
    Normalize an optional text field.
    """
    if isinstance(value, str):
        cleaned = " ".join(value.split()).strip()
        return cleaned or None

    return None


def clean_text_list(value: Any, limit: int) -> list[str]:
    """
    Normalize a list of short text items.
    """
    if not isinstance(value, list):
        return []

    cleaned_items: list[str] = []

    for item in value:
        if isinstance(item, str):
            cleaned = " ".join(item.split()).strip()
            if cleaned and cleaned not in cleaned_items:
                cleaned_items.append(cleaned)

    return cleaned_items[:limit]