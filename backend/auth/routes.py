import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_active_user
from backend.auth.email_service import send_password_reset_email
from backend.auth.models import User
from backend.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)
from backend.auth.service import (
    authenticate_user,
    change_user_password,
    create_password_reset_token,
    create_user_token,
    register_user,
    reset_user_password,
    update_user_profile,
)
from backend.database.connection import get_db

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
    try:
        return register_user(data, db)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(data.email, data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    return {
        "access_token": create_user_token(user),
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
def get_current_user(
    current_user: User = Depends(get_current_active_user),
):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user(
    data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        return update_user_profile(current_user, data, db)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error


@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    generic_message = (
        "If an account exists with that email, a password-reset link will be sent."
    )

    user = db.query(User).filter(User.email == data.email).first()

    if not user or not user.is_active:
        return {"message": generic_message}

    frontend_url = os.getenv("FRONTEND_URL")

    if not frontend_url:
        raise HTTPException(
            status_code=500,
            detail="Password-reset service is not configured.",
        )

    raw_token = create_password_reset_token(user, db)
    reset_link = f"{frontend_url.rstrip('/')}?reset_token={raw_token}"

    try:
        send_password_reset_email(user.email, reset_link)
    except Exception:
        # Invalidate the token if email delivery fails.
        from backend.auth.models import PasswordResetToken

        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used.is_(False),
        ).update({"used": True})
        db.commit()

        raise HTTPException(
            status_code=503,
            detail="Unable to send the reset email. Please try again later.",
        ) from None

    return {"message": generic_message}


@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    success = reset_user_password(data.token, data.new_password, db)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid, expired, or already-used reset link.",
        )

    return {"message": "Password successfully reset. You can now log in."}


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    success = change_user_password(
        current_user,
        data.current_password,
        data.new_password,
        db,
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect.",
        )

    return {"message": "Password changed successfully."}
