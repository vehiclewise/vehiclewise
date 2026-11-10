import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from backend.auth.models import PasswordResetToken, User
from backend.auth.schemas import UserRegister
from backend.auth.security import hash_password, verify_password
from backend.auth.token import create_access_token



def register_user(user_data: UserRegister, db: Session) -> User:
    existing_email = db.query(User).filter(User.email == user_data.email).first()

    if existing_email:
        raise ValueError("Email already registered.")

    existing_username = (
        db.query(User).filter(User.username == user_data.username).first()
    )

    if existing_username:
        raise ValueError("Username already taken.")

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        date_of_birth=user_data.date_of_birth,
        phone_number=user_data.phone_number,
        country=user_data.country,
        city=user_data.city,
        preferred_fuel=user_data.preferred_fuel,
        preferred_vehicle_type=user_data.preferred_vehicle_type,
        maximum_budget=user_data.maximum_budget,
        preferred_transmission=user_data.preferred_transmission,
        main_purpose=user_data.main_purpose,
        preferred_brands=user_data.preferred_brands,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(email: str, password: str, db: Session):
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
        return None

    return user


def create_user_token(user: User) -> str:
    return create_access_token(user.id)



def update_user_profile(user: User, user_data, db: Session) -> User:
    existing_email = (
        db.query(User)
        .filter(User.email == user_data.email, User.id != user.id)
        .first()
    )

    if existing_email:
        raise ValueError("Email already registered.")

    existing_username = (
        db.query(User)
        .filter(User.username == user_data.username, User.id != user.id)
        .first()
    )

    if existing_username:
        raise ValueError("Username already taken.")

    # Update username and email
    user.username = user_data.username
    user.email = user_data.email

    # Update only fields actually provided by the profile form
    optional_fields = [
        "full_name",
        "date_of_birth",
        "phone_number",
        "country",
        "city",
        "preferred_fuel",
        "preferred_vehicle_type",
        "maximum_budget",
        "preferred_transmission",
        "main_purpose",
        "preferred_brands",
    ]

    for field in optional_fields:
        if field in user_data.model_fields_set:
            setattr(user, field, getattr(user_data, field))

    db.commit()
    db.refresh(user)

    return user


def create_password_reset_token(user: User, db: Session) -> str:
    """Create a random, single-use password-reset token."""

    # Invalidate any previous unused reset tokens.
    previous_tokens = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used.is_(False),
        )
        .all()
    )

    for previous_token in previous_tokens:
        previous_token.used = True

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(minutes=15),
    )

    db.add(reset_record)
    db.commit()

    return raw_token


def reset_user_password(token: str, new_password: str, db: Session) -> bool:
    """Validate a reset token and securely update the user's password."""

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    reset_record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used.is_(False),
        )
        .first()
    )

    if not reset_record:
        return False

    expiry = reset_record.expires_at

    # SQLite may return a timezone-naive datetime.
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=UTC)

    if datetime.now(UTC) >= expiry:
        reset_record.used = True
        db.commit()
        return False

    user = db.query(User).filter(User.id == reset_record.user_id).first()

    if not user or not user.is_active:
        return False

    user.hashed_password = hash_password(new_password)
    reset_record.used = True

    db.commit()

    return True


def change_user_password(
    user: User,
    current_password: str,
    new_password: str,
    db: Session,
) -> bool:
    """Change the password of an authenticated user."""

    if not verify_password(current_password, user.hashed_password):
        return False

    user.hashed_password = hash_password(new_password)

    # Invalidate outstanding reset links after a password change.
    outstanding_tokens = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used.is_(False),
        )
        .all()
    )

    for reset_token in outstanding_tokens:
        reset_token.used = True

    db.commit()

    return True
