from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class WidgetConfig(db.Model):
    __tablename__ = "widget_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    u_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    w_tip: Mapped[str] = mapped_column(String(50), nullable=False)
    is_akt: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    poz: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # GridStack properties
    x: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    y: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    w: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    h: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="widgets")

    __table_args__ = (UniqueConstraint("u_id", "w_tip", name="uix_u_w_tip"),)

    def __repr__(self) -> str:
        return f"<WidgetConfig {self.w_tip} (Akt: {self.is_akt})>"
