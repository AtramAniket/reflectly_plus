import datetime
from typing import Optional
from app.extensions import db
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, func, Text, ForeignKey, JSON

class JournalAIAnalysis(db.Model):

	__tablename__ = "journal_ai_analysis"

	id: Mapped[int] = mapped_column(Integer, primary_key=True)

	entry_id: Mapped[int] = mapped_column(Integer, ForeignKey("journal_entries.id"), nullable=False)

	entry_type: Mapped[str] = mapped_column(String(50))

	summary: Mapped[str] = mapped_column(Text)

	tone: Mapped[str] = mapped_column(String(100))

	distortions: Mapped[Optional[dict]] = mapped_column(JSON)

	reframe: Mapped[str] = mapped_column(Text)

	assessment: Mapped[str] = mapped_column(String(50))

	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())