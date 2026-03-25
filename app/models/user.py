from app.extensions import db
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

class User(db.Model):

    __table__name = 'users'

    def __repr__(self):
        return f"User {self.username}"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(250), nullable=False, unique=True)