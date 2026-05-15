from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Bookmark(db.Model):
    __tablename__ = "bookmarks"

    id: Mapped[int] = mapped_column(primary_key=True)
    usr_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    icon: Mapped[str] = mapped_column(String(50), default="fa-link", nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="bookmarks")

    def __repr__(self) -> str:
        return f"<Bookmark {self.title}>"
