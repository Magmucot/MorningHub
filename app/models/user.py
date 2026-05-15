from datetime import datetime
from typing import List, Optional

from flask_login import UserMixin
from sqlalchemy import DateTime, String, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    usr_name: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    pass_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    back_img: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)

    # Погода
    weath_city: Mapped[str] = mapped_column(String(120), default="Москва", nullable=False)
    weath_lat: Mapped[Optional[float]] = mapped_column(nullable=True)
    weath_lon: Mapped[Optional[float]] = mapped_column(nullable=True)

    # AI
    ai_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ai_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # UI
    setka_lock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    theme: Mapped[str] = mapped_column(String(20), default="light", nullable=False)
    wid_cvet: Mapped[str] = mapped_column(String(20), default="#ffffff", nullable=False)
    wid_prozr: Mapped[float] = mapped_column(nullable=False, default=0.95)

    # Виджеты
    crypto_lst: Mapped[str] = mapped_column(
        String(255), default="bitcoin,ethereum,the-open-network,solana", nullable=False
    )
    val_lst: Mapped[str] = mapped_column(String(255), default="USD,EUR,CNY,GBP", nullable=False)
    clock_stile: Mapped[str] = mapped_column(String(20), default="both", nullable=False)

    widgets: Mapped[List["WidgetConfig"]] = relationship(
        "WidgetConfig",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    bookmarks: Mapped[List["Bookmark"]] = relationship(
        "Bookmark",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def set_pass(self, password: str) -> None:
        self.pass_hash = generate_password_hash(password)

    def check_pass(self, password: str) -> bool:
        return check_password_hash(self.pass_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.usr_name}>"
