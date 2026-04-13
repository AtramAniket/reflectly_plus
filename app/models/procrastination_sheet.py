import datetime
from typing import Optional

from app.extensions import db
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, func, Text, ForeignKey, Boolean


class ProcrastinationSheet(db.Model):
    __tablename__ = "procrastination_sheets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now()
    )

    user = relationship("User", back_populates="procrastination_sheets")

    tasks: Mapped[list["ProcrastinationTask"]] = relationship(
        "ProcrastinationTask",
        back_populates="sheet",
        cascade="all, delete-orphan",
        order_by="ProcrastinationTask.created_at.asc()"
    )

    def __repr__(self):
        return f"<ProcrastinationSheet {self.id}: {self.title}>"


class ProcrastinationTask(db.Model):
    __tablename__ = "procrastination_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    sheet_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("procrastination_sheets.id", ondelete="CASCADE"),
        nullable=False
    )

    task_name: Mapped[str] = mapped_column(String(255), nullable=False)

    avoidance_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resistance_thoughts: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tiny_step: Mapped[str] = mapped_column(Text, nullable=False)

    expected_difficulty: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_satisfaction: Mapped[int] = mapped_column(Integer, nullable=False)

    actual_difficulty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_satisfaction: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    reflection: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now()
    )

    sheet = relationship("ProcrastinationSheet", back_populates="tasks")

    def __repr__(self):
        return f"<ProcrastinationTask {self.id}: {self.task_name}>"