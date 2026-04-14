from datetime import datetime

from app.extensions import db
from sqlalchemy import String, Integer, ForeignKey, Boolean, DateTime, Text, text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Habit(db.Model):
    __tablename__ = 'habits'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)

    is_archived: Mapped[bool] = mapped_column(
    Boolean,
    nullable=False,
    default=False,
    server_default=text("0")
    )

    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    archived_reason: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    archived_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    logs = relationship('HabitLog', back_populates='habit', cascade='all, delete-orphan')

    user = relationship('User', back_populates='habits')