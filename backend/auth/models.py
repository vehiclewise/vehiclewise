from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    full_name: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)

    phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True)

    country: Mapped[str] = mapped_column(String(100), nullable=False, default="")

    city: Mapped[str | None] = mapped_column(String(100), nullable=True)

    preferred_fuel: Mapped[str] = mapped_column(
        String(30), nullable=False, default="Any"
    )

    preferred_vehicle_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="Any"
    )

    maximum_budget: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    preferred_transmission: Mapped[str] = mapped_column(
        String(30), nullable=False, default="Any"
    )

    main_purpose: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Other"
    )

    preferred_brands: Mapped[str] = mapped_column(
        String(500), nullable=False, default=""
    )

    is_active: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
