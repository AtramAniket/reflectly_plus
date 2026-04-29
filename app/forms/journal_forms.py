from flask_wtf import FlaskForm
from wtforms import HiddenField, IntegerField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange


class SimpleJournalForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[
            DataRequired(message="Title is required."),
            Length(max=120, message="Title must be 120 characters or fewer."),
        ],
    )

    mood_score = IntegerField(
        "Mood score",
        validators=[
            DataRequired(message="Mood score is required."),
            NumberRange(min=1, max=10, message="Mood score must be between 1 and 10."),
        ],
    )

    content = HiddenField(
        "Content",
        validators=[
            DataRequired(message="Content is required to save journal entry."),
        ],
    )