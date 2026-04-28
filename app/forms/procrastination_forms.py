from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class ProcrastinationSheetForm(FlaskForm):
    title = StringField(
        "What should this worksheet be called?",
        validators=[
            DataRequired(message="Please give this worksheet a title."),
            Length(max=255, message="Title must be 255 characters or fewer.")
        ],
        render_kw={
            "placeholder": "Example: This Week's Avoided Tasks"
        }
    )

    note = TextAreaField(
        "What kind of tasks are you collecting?",
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


class ProcrastinationTaskForm(FlaskForm):
    task_name = StringField(
        "What task are you avoiding?",
        validators=[
            DataRequired(message="Please name the task."),
            Length(max=255, message="Task name must be 255 characters or fewer.")
        ],
        render_kw={
            "placeholder": "Example: Finish the dashboard polish"
        }
    )

    avoidance_reason = TextAreaField(
        "Why does this task feel hard right now?",
        validators=[
            Optional(),
            Length(max=1000, message="Keep this under 1000 characters.")
        ],
        render_kw={
            "placeholder": "Example: It feels vague, and I am not sure where to start.",
            "rows": 3
        }
    )

    resistance_thoughts = TextAreaField(
        "What thought keeps pulling you away from it?",
        validators=[
            Optional(),
            Length(max=1000, message="Keep this under 1000 characters.")
        ],
        render_kw={
            "placeholder": "Example: This will take forever, and I might mess it up.",
            "rows": 3
        }
    )

    tiny_step = TextAreaField(
        "What is the smallest first step?",
        validators=[
            DataRequired(message="Please add one tiny first step."),
            Length(max=1000, message="Keep this under 1000 characters.")
        ],
        render_kw={
            "placeholder": "Example: Open the file and fix just one section for 10 minutes.",
            "rows": 3
        }
    )

    expected_difficulty = IntegerField(
        "Expected difficulty",
        validators=[
            DataRequired(message="Please rate expected difficulty."),
            NumberRange(min=0, max=10, message="Difficulty must be between 0 and 10.")
        ],
        render_kw={
            "min": 0,
            "max": 10
        }
    )

    expected_satisfaction = IntegerField(
        "Expected satisfaction",
        validators=[
            DataRequired(message="Please rate expected satisfaction."),
            NumberRange(min=0, max=10, message="Satisfaction must be between 0 and 10.")
        ],
        render_kw={
            "min": 0,
            "max": 10
        }
    )

    submit = SubmitField("Add task to worksheet")

class CompleteProcrastinationTaskForm(FlaskForm):
    actual_difficulty = IntegerField(
        "How difficult was it actually?",
        validators=[
            DataRequired(message="Please rate actual difficulty."),
            NumberRange(min=0, max=10, message="Difficulty must be between 0 and 10.")
        ],
        render_kw={"min": 0, "max": 10}
    )

    actual_satisfaction = IntegerField(
        "How satisfying did it feel afterward?",
        validators=[
            DataRequired(message="Please rate actual satisfaction."),
            NumberRange(min=0, max=10, message="Satisfaction must be between 0 and 10.")
        ],
        render_kw={"min": 0, "max": 10}
    )

    reflection = TextAreaField(
        "What did you notice?",
        validators=[
            Optional(),
            Length(max=1200, message="Reflection must be 1200 characters or fewer.")
        ],
        render_kw={
            "placeholder": "Example: It felt easier once I started. The hardest part was opening the file.",
            "rows": 4
        }
    )

    submit = SubmitField("Save review")