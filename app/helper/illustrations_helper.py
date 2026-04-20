import os
import random
from typing import Optional

from flask import current_app, url_for


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


def get_mood_bucket_from_score(score: Optional[float]) -> str:
    """
    Maps a mood score to an illustration bucket.
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
    return MOOD_ILLUSTRATION_MAP.get(bucket, MOOD_ILLUSTRATION_MAP["calm"])


def static_file_exists(relative_path: str) -> bool:
    """
    Checks whether a static asset exists inside the app's static folder.
    """
    absolute_path = os.path.join(current_app.static_folder, relative_path)
    return os.path.exists(absolute_path)


def get_existing_scene_paths(bucket: str) -> list[str]:
    """
    Returns only the paths that physically exist in static/.
    """
    configured_paths = get_scene_paths_for_bucket(bucket)
    return [path for path in configured_paths if static_file_exists(path)]


def choose_scene_path(score: Optional[float], seed_value: Optional[str] = None) -> Optional[str]:
    """
    Picks a stable-ish scene path for the given score.
    Returns None if no file exists yet.
    """
    bucket = get_mood_bucket_from_score(score)
    existing_paths = get_existing_scene_paths(bucket)

    if not existing_paths:
        return None

    if seed_value:
        seeded_random = random.Random(seed_value)
        return seeded_random.choice(existing_paths)

    return random.choice(existing_paths)


def build_scene_payload(score: Optional[float], seed_value: Optional[str] = None) -> dict:
    """
    Returns a template-friendly illustration payload.
    """
    bucket = get_mood_bucket_from_score(score)
    chosen_path = choose_scene_path(score=score, seed_value=seed_value)

    if chosen_path:
        return {
            "bucket": bucket,
            "has_image": True,
            "image_path": chosen_path,
            "image_url": url_for("static", filename=chosen_path),
            "alt": build_scene_alt_text(bucket),
        }

    return {
        "bucket": bucket,
        "has_image": False,
        "image_path": None,
        "image_url": None,
        "alt": build_scene_alt_text(bucket),
    }


def build_scene_alt_text(bucket: str) -> str:
    alt_map = {
        "low": "A soft reflective illustration for lower-energy moments.",
        "cloudy": "A calm, slightly muted illustration for mixed or heavy days.",
        "calm": "A balanced and peaceful illustration for steady days.",
        "bright": "A warm and uplifting illustration for brighter days.",
        "growth": "A hopeful and vibrant illustration for strong, positive days.",
    }
    return alt_map.get(bucket, "A calm reflective illustration.")