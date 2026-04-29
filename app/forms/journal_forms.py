from flask_wtf import FlaskForm
from wtforms import HiddenField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError


class SimpleJournalForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[
            DataRequired(message="Title is required."),
            Length(max=80, message="Title must be 80 characters or fewer."),
        ],
    )

    mood_score = HiddenField(
        "Mood score",
        validators=[DataRequired(message="Mood score is required.")],
    )

    content = HiddenField(
        "Content",
        validators=[DataRequired(message="Content is required to save journal entry.")],
    )

    def validate_mood_score(self, field):
        try:
            score = int(field.data)
        except (TypeError, ValueError):
            raise ValidationError("Mood score must be a valid number.")

        if score < 1 or score > 10:
            raise ValidationError("Mood score must be between 1 and 10.")

class GratitudeJournalForm(FlaskForm):
    gratitude_1 = TextAreaField(
        "What are you grateful for today?",
        validators=[DataRequired(message="Please answer the first gratitude prompt.")],
    )

    gratitude_2 = TextAreaField(
        "Who or what made today lighter?",
        validators=[DataRequired(message="Please answer the second gratitude prompt.")],
    )

    gratitude_3 = TextAreaField(
        "What small moment do you want to remember?",
        validators=[DataRequired(message="Please answer the third gratitude prompt.")],
    )

    mood_score = HiddenField(
        "Mood score",
        validators=[DataRequired(message="Mood score is required.")],
    )

    def validate_mood_score(self, field):
        try:
            score = int(field.data)
        except (TypeError, ValueError):
            raise ValidationError("Mood score must be a valid number.")

        if score < 1 or score > 10:
            raise ValidationError("Mood score must be between 1 and 10.")

class ReflectionJournalForm(FlaskForm):
    went_well = TextAreaField(
        "What went well today?",
        validators=[DataRequired(message="Please answer what went well today.")],
    )

    challenging = TextAreaField(
        "What felt difficult?",
        validators=[DataRequired(message="Please answer what felt difficult.")],
    )

    tomorrow = TextAreaField(
        "What will you carry into tomorrow?",
        validators=[DataRequired(message="Please answer what you'll carry into tomorrow.")],
    )

    mood_score = HiddenField(
        "Mood score",
        validators=[DataRequired(message="Mood score is required.")],
    )

    def validate_mood_score(self, field):
        try:
            score = int(field.data)
        except (TypeError, ValueError):
            raise ValidationError("Mood score must be a valid number.")

        if score < 1 or score > 10:
            raise ValidationError("Mood score must be between 1 and 10.")