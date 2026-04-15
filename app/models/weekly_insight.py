from typing import Optional
from app.extensions import db
from datetime import datetime, date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Text, String, Integer, Boolean, JSON, DateTime, Date, ForeignKey, UniqueConstraint, func 

class WeeklyInsight(db.Model):

	__tablename__ = 'weekly_insights'

	# Unique constraints
	__table_args__ = (
		UniqueConstraint("user_id", "week_start", name="uq_weekly_insight_user_week"),
		)

	id: Mapped[int] = mapped_column(Integer, primary_key=True)

	# Foreign Key
	user_id : Mapped[int] = mapped_column(Integer,\
											ForeignKey("users.id",\
											ondelete="CASCADE"),\
											nullable=False,\
											index=True)

	week_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)

	week_end: Mapped[date] = mapped_column(Date, nullable=False)

	summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

	patterns: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)

	contradictions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

	suggestions: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)

	sufficiency_level: Mapped[str] = mapped_column(String(20), nullable=False, default='insufficient')

	confidence_level: Mapped[str] = mapped_column(String(20), nullable=False, default='low')

	contradiction_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

	signals_used: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

	structured_context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

	generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())



	# Relationship with User
	user = relationship("User", back_populates="weekly_insights")


	def __repr__(self):
		return (
				f"<WeeklyInsight id={self.id} user_id={self.user_id} "
				f"week_start={self.week_start} sufficiency={self.sufficiency_level}>"
			)