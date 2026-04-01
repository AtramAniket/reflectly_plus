import datetime
from app.extensions import db
from sqlalchemy import Integer, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

class HabitLog(db.Model):

	__tablename__ = 'habit_logs'

	id: Mapped[int] = mapped_column(Integer, primary_key=True)

	date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())

	completed: Mapped[bool] = mapped_column(Boolean, default=False)

	habit_id: Mapped[int] = mapped_column(ForeignKey('habits.id'), nullable=False)

	habit = relationship('Habit', back_populates='logs')

