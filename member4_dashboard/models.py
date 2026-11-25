from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class Bookmark(Base):
    __tablename__ = "bookmarks"
    __table_args__ = (UniqueConstraint("profile_id", "vehicle_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    vehicle_key: Mapped[str] = mapped_column(String(255), nullable=False)
    vehicle_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vehicle_data: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    searched_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SavedComparison(Base):
    __tablename__ = "saved_comparisons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    vehicle_names: Mapped[str] = mapped_column(Text, nullable=False)
    vehicle_data: Mapped[str] = mapped_column(Text, nullable=False)
    saved_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
