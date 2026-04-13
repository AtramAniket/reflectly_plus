import datetime
from typing import Optional
from app.extensions import db
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, func, Text, ForeignKey, JSON

class ProcrastinationSheet(db.Model):

	__tablename__ = 'procrastination_sheet'

	id: Mapped[int] = mapped_column(Integer, primary_key=True)

	user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

	task_name: Mapped[str] = mapped_column(String(500), nullable=False)
	avoidence_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

	expected_difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
	expected_statisfaction: Mapped[int] = mapped_column(Integer, nullable=False)

	resistance_thoughts: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
	tiny_steps: Mapped[str] = mapped_column(Text, nullable=False)

	actual_difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
	actual_statisfaction: Mapped[int] = mapped_column(Integer, nullable=False)

	reflection: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

	created_at: Mapped[datetime] = mapped_column(
	    DateTime(timezone=True),
	    nullable=False,
	    server_default=func.now()
	)

	updated_at: Mapped[Optional[datetime]] = mapped_column(
	    DateTime(timezone=True),
	    nullable=True,
	    onupdate=func.now()
	)

	user = relationship("User", back_populates="procrastination_sheets")

	def __repr__(self):
		return f"Sheet {self.id}"