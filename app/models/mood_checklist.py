import datetime
from typing import Optional
from app.extensions import db
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, func, Text, ForeignKey, JSON

class MoodChecklistResult(db.Model, UserMixin):

	__tablename__ = "mood_checklist_results"

	id: Mapped[int] = mapped_column(Integer, primary_key=True)

	user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

	answers: Mapped[dict] = mapped_column(JSON, nullable=False)

	total_score: Mapped[int] = mapped_column(Integer, nullable=False)

	note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

	# Relationship with user
	user = relationship("User", back_populates="mood_checklist_results")