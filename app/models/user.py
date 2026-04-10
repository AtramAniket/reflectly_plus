import datetime
from app.extensions import db
from flask_login import UserMixin
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):

    __tablename__ = 'users'

    def __repr__(self):
        return f"User {self.email}"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationship with JournalEntry
    entries: Mapped[list['JournalEntry']] = relationship('JournalEntry', back_populates='user', cascade='all, delete-orphan')

    # Relationship with Habit
    habits = relationship('Habit', back_populates='user', cascade='all, delete-orphan')

    # Relationship with MoodChecklistResults
    mood_checklist_results = relationship('MoodChecklistResult', back_populates='user',cascade='all, delete-orphan', order_by='desc(MoodChecklistResult.created_at')

    def set_password(self, raw_password_text) -> None:

        self.password_hash = generate_password_hash(raw_password_text, method="pbkdf2:sha256:600000", salt_length=8)


    def check_password(self, raw_password_text) -> bool:

        return check_password_hash(self.password_hash, raw_password_text)