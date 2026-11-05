from sqlalchemy.orm import Session

from backend.auth.models import User
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
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(email: str, password: str, db: Session):
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


def create_user_token(user: User) -> str:
    return create_access_token(user.id)


def update_user_profile(user: User, user_data, db: Session) -> User:
    existing_email = (
        db.query(User).filter(User.email == user_data.email, User.id != user.id).first()
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

    user.username = user_data.username
    user.email = user_data.email

    db.commit()
    db.refresh(user)

    return user
