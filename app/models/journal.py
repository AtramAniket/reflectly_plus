import datetime
from typing import Optional
from app.extensions import db
from flask_login import UserMixin
from sqlalchemy import String, Integer, DateTime, func, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column,relationship

class JournalEntry(UserMixin, db.Model):

	__tablename__ = 'journal_entries'

	id: Mapped[int] =  mapped_column(Integer, primary_key=True)

	entry_type: Mapped[str] = mapped_column(String(50), nullable=False, default='simple')

	title: Mapped[str] = mapped_column(String(250), nullable=False)

	content: Mapped[str] = mapped_column(Text, nullable=False)

	mood_score: Mapped[int] =  mapped_column(Integer, nullable=False)

	image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

	# Foreign ket to user
	user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)

	# Relationship(backref)
	user: Mapped['User'] = relationship('User', back_populates='entries')

	
	def __repr__(self):
		return f'<JournalEntry {self.id}>'