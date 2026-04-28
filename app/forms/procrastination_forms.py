from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class ProcrastinationSheetForm(FlaskForm):
    title = StringField(
        "Worksheet title",
        validators=[
            DataRequired(message="Please give this worksheet a title."),
            Length(max=255, message="Title must be 255 characters or fewer.")
        ],
        render_kw={
            "placeholder": "Example: This Week's Avoided Tasks"
        }
    )

    note = TextAreaField(
        "Worksheet note",
        validators=[
            Optional(),
            Length(max=1000, message="Note must be 1000 characters or fewer.")
        ],
        render_kw={
            "placeholder": "Example: Work tasks I keep postponing because they feel bigger than they are.",
            "rows": 4
        }
    )

    submit = SubmitField("Create worksheet")