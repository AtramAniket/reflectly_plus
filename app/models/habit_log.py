from datetime import date, datetime
from app.extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Date, DateTime, ForeignKey, Boolean, func, UniqueConstraint

class HabitLog(db.Model):

	__tablename__ = 'habit_logs'

	__table_args__ = (
	    UniqueConstraint('habit_id', 'date', name='unique_habit_per_day'),
	)

	id: Mapped[int] = mapped_column(Integer, primary_key=True)

	date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)

	completed: Mapped[bool] = mapped_column(Boolean, default=False)

	habit_id: Mapped[int] = mapped_column(ForeignKey('habits.id'), nullable=False)

	habit = relationship('Habit', back_populates='logs')

	created_at: Mapped[datetime] = mapped_column(
	    DateTime(timezone=True),
	    nullable=False,
	    server_default=func.now()
	)

