import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.user import User


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


class SignupForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(message="Please choose a username."),
            Length(min=3, max=20, message="Username must be between 3 and 20 characters.")
        ]
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Please enter your email."),
            Email(message="Please enter a valid email address."),
            Length(max=150, message="Email must be under 150 characters.")
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Please create a password."),
            Length(min=8, message="Password must be at least 8 characters.")
        ]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match.")
        ]
    )

    submit = SubmitField("Create account")

    def validate_username(self, username):
        cleaned_username = username.data.strip()

        if not USERNAME_PATTERN.match(cleaned_username):
            raise ValidationError("Username can only contain letters, numbers, and underscores.")

        existing_user = User.query.filter_by(username=cleaned_username).first()
        if existing_user:
            raise ValidationError("That username is already taken.")

        username.data = cleaned_username

    def validate_email(self, email):
        cleaned_email = email.data.strip().lower()

        existing_user = User.query.filter_by(email=cleaned_email).first()
        if existing_user:
            raise ValidationError("An account with this email already exists.")

        email.data = cleaned_email


class LoginForm(FlaskForm):
    identifier = StringField(
        "Email or username",
        validators=[
            DataRequired(message="Please enter your email or username.")
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Please enter your password.")
        ]
    )

    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")