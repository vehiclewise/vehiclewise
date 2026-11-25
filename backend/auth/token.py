import os
from datetime import UTC, datetime, timedelta

import jwt
from dotenv import load_dotenv

load_dotenv()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(user_id: int) -> str:
    """Generate a JWT access token for an authenticated user."""

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY is not configured.")

    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(payload, secret_key, algorithm=ALGORITHM)


def verify_access_token(token: str) -> dict:
    """Verify a JWT token and return its payload."""

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY is not configured.")

    return jwt.decode(token, secret_key, algorithms=[ALGORITHM])
