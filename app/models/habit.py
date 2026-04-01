from app.extensions import db
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Habit(db.Model):

	__tablename__ = 'habits'

	id: Mapped[int] = mapped_column(Integer, primary_key=True)

	name: Mapped[str] = mapped_column(String(200), nullable=False)

	user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

	logs  = relationship('HabitLog', back_populates='habit', cascade='all, delete-orphan')