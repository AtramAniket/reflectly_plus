from collections import defaultdict

CHECKLIST_QUESTIONS = [
    {
        "key": "motivation",
        "title": "Motivation difficulty",
        "text": "I found it hard to feel motivated to do things I normally need or want to do.",
        "category_key": "energy_motivation",
        "category_label": "Energy & Motivation",
    },
    {
        "key": "sadness_fatigue",
        "title": "Emotional heaviness",
        "text": "I felt weighed down by sadness, emptiness, or emotional fatigue.",
        "category_key": "emotional_weight",
        "category_label": "Emotional Weight",
    },
    {
        "key": "self_criticism",
        "title": "Self-pressure",
        "text": "I was overly harsh or critical toward myself.",
        "category_key": "self_connection",
        "category_label": "Self & Connection",
    },
    {
        "key": "setbacks_feeling_heavier",
        "title": "Sensitivity to setbacks",
        "text": "Small setbacks felt bigger or heavier than they usually would.",
        "category_key": "emotional_weight",
        "category_label": "Emotional Weight",
    },
    {
        "key": "focus_presence",
        "title": "Focus difficulty",
        "text": "I found it difficult to focus or stay mentally present.",
        "category_key": "mind_focus",
        "category_label": "Mind & Focus",
    },
    {
        "key": "tension_overwhelm",
        "title": "Stress overload",
        "text": "I felt tense, restless, or mentally overwhelmed.",
        "category_key": "emotional_weight",
        "category_label": "Emotional Weight",
    },
    {
        "key": "enjoyment_comfort",
        "title": "Reduced enjoyment",
        "text": "I struggled to enjoy things that normally give me comfort or satisfaction.",
        "category_key": "energy_motivation",
        "category_label": "Energy & Motivation",
    },
    {
        "key": "disconnection",
        "title": "Social disconnection",
        "text": "I felt disconnected from other people, even when I wasn’t alone.",
        "category_key": "self_connection",
        "category_label": "Self & Connection",
    },
    {
        "key": "expecting_worst",
        "title": "Worry spirals",
        "text": "I found myself expecting things to go badly or assuming the worst.",
        "category_key": "mind_focus",
        "category_label": "Mind & Focus",
    },
    {
        "key": "hopefulness",
        "title": "Reduced hope",
        "text": "It felt harder than usual to believe things could improve.",
        "category_key": "self_connection",
        "category_label": "Self & Connection",
    },
]

SCORE_LABELS = {
    0: "Not at all",
    1: "A little",
    2: "Sometimes",
    3: "Often",
    4: "Very much",
}

CATEGORY_DESCRIPTIONS = {
    "energy_motivation": "How easy or difficult it may have felt to get going and enjoy everyday life.",
    "emotional_weight": "How stress, emotional heaviness, or overwhelm may have been showing up.",
    "mind_focus": "How your attention, presence, and thought patterns may have felt.",
    "self_connection": "How you may have been relating to yourself, other people, and the future.",
}


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


def get_checklist_question_texts() -> list[str]:
    return [question["text"] for question in CHECKLIST_QUESTIONS]


def get_checklist_interpretation(question_key: str, score: int) -> str:
    interpretations = {
        "motivation": {
            0: "You seem to be feeling motivated and able to engage with the things you need or want to do.",
            1: "You may have noticed a slight dip in motivation at times, but it does not seem to be weighing too heavily on you.",
            2: "Motivation may have felt somewhat uneven lately, with some tasks taking more effort than usual to begin or follow through on.",
            3: "You may have been struggling fairly often with motivation, even for things that normally matter to you.",
            4: "Low motivation seems to have been showing up strongly, making it harder to engage with everyday responsibilities or interests.",
        },
        "sadness_fatigue": {
            0: "Sadness or emotional heaviness does not seem to have been a strong presence in this check-in.",
            1: "There may have been a little emotional heaviness at times, though it does not appear to have been dominant.",
            2: "Feelings of sadness, emptiness, or emotional fatigue may have been present on and off lately.",
            3: "Emotional heaviness seems to have been showing up fairly often and may have taken some energy to carry.",
            4: "Sadness, emptiness, or emotional fatigue appears to have been strongly present for you in this check-in.",
        },
        "self_criticism": {
            0: "You do not seem to be dealing with strong self-critical thoughts right now.",
            1: "Self-criticism may have surfaced occasionally, but it does not appear to have been especially strong.",
            2: "You may have been somewhat harder on yourself lately than you would like to be.",
            3: "Self-critical thoughts seem to have been showing up fairly often and may have affected how you saw yourself.",
            4: "Harsh self-judgment appears to have been strongly present in this check-in.",
        },
        "setbacks_feeling_heavier": {
            0: "Setbacks do not seem to have felt unusually heavy for you right now.",
            1: "Some frustrations may have felt a little harder than usual, but not dramatically so.",
            2: "Smaller setbacks may have felt more draining or discouraging than they normally would.",
            3: "Setbacks seem to have felt heavier fairly often, which may have made everyday stress harder to absorb.",
            4: "Even small difficulties appear to have been landing with unusual weight for you in this check-in.",
        },
        "focus_presence": {
            0: "Your focus and ability to stay mentally present seem fairly steady right now.",
            1: "You may have noticed a little mental drifting or difficulty concentrating at times.",
            2: "Focus may have felt inconsistent lately, with some difficulty staying mentally present.",
            3: "Difficulty focusing seems to have been showing up fairly often and may have made it harder to stay grounded in the moment.",
            4: "Focus and mental presence appear to have been strongly affected in this check-in.",
        },
        "tension_overwhelm": {
            0: "Tension or overwhelm does not seem to have been a major part of this check-in.",
            1: "There may have been some mild tension or restlessness, but it does not appear to have been overwhelming.",
            2: "Stress, tension, or mental overwhelm may have been showing up from time to time lately.",
            3: "Feelings of tension or overwhelm seem to have been fairly present and may have made it harder to feel settled.",
            4: "Tension, restlessness, or mental overwhelm appears to have been strongly present for you in this check-in.",
        },
        "enjoyment_comfort": {
            0: "Comfort, enjoyment, and everyday sources of satisfaction do not seem heavily blocked right now.",
            1: "There may have been a slight dip in enjoyment at times, but some sense of comfort still seems available to you.",
            2: "Enjoyment may have felt less accessible lately, with some difficulty fully settling into things that usually help.",
            3: "You may have been struggling fairly often to enjoy things that would normally bring comfort or satisfaction.",
            4: "A noticeable loss of enjoyment or comfort seems to have been strongly present in this check-in.",
        },
        "disconnection": {
            0: "You do not seem to be feeling strongly disconnected from others right now.",
            1: "There may have been moments of distance from others, though not in a way that seems especially strong.",
            2: "A sense of disconnection may have shown up at times, even when other people were around.",
            3: "Feeling emotionally distant from others seems to have been showing up fairly often in this check-in.",
            4: "Disconnection from others appears to have been strongly present for you, even in company.",
        },
        "expecting_worst": {
            0: "Worst-case thinking does not seem to have been strongly shaping your outlook right now.",
            1: "Some worry may have surfaced now and then, but it does not appear to have taken over your thinking.",
            2: "You may have found yourself slipping into worry or expecting negative outcomes from time to time.",
            3: "Worry and worst-case thinking seem to have been fairly present and may have influenced how situations felt to you.",
            4: "Expecting things to go badly appears to have been strongly present in this check-in.",
        },
        "hopefulness": {
            0: "Your sense that things can improve seems fairly intact right now.",
            1: "There may have been a few moments of doubt, but some sense of hope still seems present.",
            2: "Hopefulness may have felt a bit harder to hold onto lately, even if not entirely absent.",
            3: "A reduced sense of hope seems to have been showing up fairly often in this check-in.",
            4: "It appears to have felt especially difficult to believe that things could improve right now.",
        },
    }

    return interpretations[question_key][score]


def get_checklist_response_tone(score: int) -> str:
    if score == 0:
        return "steady"
    if score == 1:
        return "mild"
    if score == 2:
        return "noticeable"
    if score == 3:
        return "elevated"
    return "high"


def get_checklist_response_label(score: int) -> str:
    if score == 0:
        return "Minimal"
    if score == 1:
        return "Mild"
    if score == 2:
        return "Noticeable"
    if score == 3:
        return "Elevated"
    return "Strongly present"


def build_checklist_response_items(answers: dict) -> list[dict]:
    items = []

    for idx, question in enumerate(CHECKLIST_QUESTIONS):
        score = int(answers.get(f"q_{idx}", 0))

        items.append({
            "key": question["key"],
            "title": question["title"],
            "question": question["text"],
            "category_key": question["category_key"],
            "category_label": question["category_label"],
            "category_description": CATEGORY_DESCRIPTIONS[question["category_key"]],
            "score": score,
            "label": get_checklist_response_label(score),
            "tone": get_checklist_response_tone(score),
            "summary": get_checklist_interpretation(question["key"], score),
        })

    return items


def build_grouped_checklist_sections(answers: dict) -> list[dict]:
    items = build_checklist_response_items(answers)
    grouped = defaultdict(list)

    for item in items:
        grouped[item["category_key"]].append(item)

    category_meta = {
        "emotional_weight": {
            "label": "Emotional Weight",
            "description": CATEGORY_DESCRIPTIONS["emotional_weight"],
        },
        "self_connection": {
            "label": "Self & Connection",
            "description": CATEGORY_DESCRIPTIONS["self_connection"],
        },
        "energy_motivation": {
            "label": "Energy & Motivation",
            "description": CATEGORY_DESCRIPTIONS["energy_motivation"],
        },
        "mind_focus": {
            "label": "Mind & Focus",
            "description": CATEGORY_DESCRIPTIONS["mind_focus"],
        },
    }

    ordered_category_keys = [
        "energy_motivation",
        "mind_focus",
        "emotional_weight",
        "self_connection",
    ]

    ordered_sections = []

    for category_key in ordered_category_keys:
        ordered_sections.append({
            "category_key": category_key,
            "category_label": category_meta[category_key]["label"],
            "category_description": category_meta[category_key]["description"],
            "items": grouped[category_key],
        })

    return ordered_sections