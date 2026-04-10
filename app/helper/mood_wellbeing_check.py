CHECKLIST_QUESTIONS = [
    "I found it hard to feel motivated to do things I normally need or want to do.",
    "I felt weighed down by sadness, emptiness, or emotional fatigue.",
    "I was overly harsh or critical toward myself.",
    "Small setbacks felt bigger or heavier than they usually would.",
    "I found it difficult to focus or stay mentally present.",
    "I felt tense, restless, or mentally overwhelmed.",
    "I struggled to enjoy things that normally give me comfort or satisfaction.",
    "I felt disconnected from other people, even when I wasn’t alone.",
    "I found myself expecting things to go badly or assuming the worst.",
    "It felt harder than usual to believe things could improve."
]


def get_checklist_feedback(total_score: int) -> dict:
    if total_score <= 7:
        return {
            "label": "Doing fairly okay",
            "tone": "low",
            "message": (
                "Your responses suggest you're managing reasonably well overall. "
                "Regular check-ins can still help you notice patterns and take care of yourself early."
            )
        }
    elif total_score <= 15:
        return {
            "label": "Mild emotional strain",
            "tone": "mild",
            "message": (
                "Your responses suggest some emotional strain. Rest, journaling, supportive routines, "
                "and talking things through with someone you trust may help."
            )
        }
    elif total_score <= 23:
        return {
            "label": "Moderate emotional difficulty",
            "tone": "moderate",
            "message": (
                "Your responses suggest a more noticeable level of distress. "
                "If this has been persistent, it may help to talk with someone you trust or consider professional support."
            )
        }
    elif total_score <= 31:
        return {
            "label": "High emotional strain",
            "tone": "high",
            "message": (
                "Your responses suggest significant emotional strain right now. "
                "If these feelings are affecting daily life, reaching out to a mental health professional could be helpful."
            )
        }
    else:
        return {
            "label": "Severe emotional strain",
            "tone": "severe",
            "message": (
                "Your responses suggest very high emotional strain right now. "
                "Please consider reaching out to a licensed mental health professional or a trusted support person soon."
            )
        }