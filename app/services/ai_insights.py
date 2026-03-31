from openai import OpenAI
from flask import current_app

client = OpenAI()

def generate_insight(avg_mood, trend, entries):
    try:
        # Prepare recent entries (limit for token safety)
        recent_entries = entries[-5:]

        entry_text = "\n".join(
            [f"- {e.title}: mood {e.mood_score}" for e in recent_entries]
        )

        prompt = f"""
        You are a journaling insight generator.

        Your job is to reflect observations back to the user.

        Keep it:
        - Short (2 sentences max)
        - Calm, supportive, and observational
        - NOT conversational
        - Do NOT ask questions
        - Do NOT invite the user to chat

        User data:
        - Average mood: {avg_mood}
        - Trend: {trend}

        Recent entries:
        {entry_text}

        Instructions:
        - If mood is declining → gently acknowledge it
        - If improving → positively reinforce it
        - Focus on observation, not advice
        - No questions at all
        - No phrases like "want to talk" or "you can share"

        Just return the insight.
        """

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a supportive mental wellness assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )

        return response.choices[0].message.content

    except Exception as e:
        print("OpenAI Error:", e)
        return "Insights unavailable right now."