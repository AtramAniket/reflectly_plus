import random
from typing import Optional

from flask import url_for


MOOD_ILLUSTRATION_MAP = {
    "low": [
        "images/moods/low/low_1.png",
        "images/moods/low/low_2.png",
        "images/moods/low/low_3.png",
    ],
    "cloudy": [
        "images/moods/cloudy/cloudy_1.png",
        "images/moods/cloudy/cloudy_2.png",
        "images/moods/cloudy/cloudy_3.png",
    ],
    "calm": [
        "images/moods/calm/calm_1.png",
        "images/moods/calm/calm_2.png",
        "images/moods/calm/calm_3.png",
    ],
    "bright": [
        "images/moods/bright/bright_1.png",
        "images/moods/bright/bright_2.png",
        "images/moods/bright/bright_3.png",
    ],
    "growth": [
        "images/moods/growth/growth_1.png",
        "images/moods/growth/growth_2.png",
        "images/moods/growth/growth_3.png",
    ],
}

DEFAULT_MOOD_SCENE = "images/moods/calm/calm_1.png"


def get_mood_bucket_from_score(score: Optional[float]) -> str:
    """
    Maps a mood score to a mood illustration bucket.

    Current ranges:
    0-4   -> low
    5-8   -> cloudy
    9-12  -> calm
    13-16 -> bright
    17+   -> growth
    """
    if score is None:
        return "calm"

    if score <= 4:
        return "low"
    if score <= 8:
        return "cloudy"
    if score <= 12:
        return "calm"
    if score <= 16:
        return "bright"
    return "growth"


def get_scene_paths_for_bucket(bucket: str) -> list[str]:
    """
    Returns the configured file paths for a bucket.
    Falls back to calm if bucket is missing.
    """
    return MOOD_ILLUSTRATION_MAP.get(bucket, MOOD_ILLUSTRATION_MAP["calm"])


def choose_scene_path(score: Optional[float], seed_value: Optional[str] = None) -> str:
    """
    Picks a stable-ish scene path for the given score.

    If seed_value is passed, the selection becomes deterministic for that value.
    Useful for weekly pages where you want the same scene for the same week.
    """
    bucket = get_mood_bucket_from_score(score)
    paths = get_scene_paths_for_bucket(bucket)

    if not paths:
        return DEFAULT_MOOD_SCENE

    if seed_value:
        seeded_random = random.Random(seed_value)
        return seeded_random.choice(paths)

    return random.choice(paths)


def build_scene_payload(score: Optional[float], seed_value: Optional[str] = None) -> dict:
    """
    Returns a full payload that templates can use directly.
    """
    bucket = get_mood_bucket_from_score(score)
    chosen_path = choose_scene_path(score=score, seed_value=seed_value)

    return {
        "bucket": bucket,
        "image_path": chosen_path,
        "image_url": url_for("static", filename=chosen_path),
        "alt": build_scene_alt_text(bucket),
    }


def build_scene_alt_text(bucket: str) -> str:
    """
    Accessible alt text for the current scene.
    """
    alt_map = {
        "low": "A soft reflective illustration for lower-energy moments.",
        "cloudy": "A calm, slightly muted illustration for mixed or heavy days.",
        "calm": "A balanced and peaceful illustration for steady days.",
        "bright": "A warm and uplifting illustration for brighter days.",
        "growth": "A hopeful and vibrant illustration for strong, positive days.",
    }
    return alt_map.get(bucket, "A calm reflective illustration.")