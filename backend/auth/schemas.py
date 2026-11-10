
from datetime import date
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    # Account details
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    # Personal information
    full_name: str = Field(default="", max_length=100)
    date_of_birth: date | None = None
    phone_number: str | None = Field(default=None, max_length=30)
    country: str = Field(default="", max_length=100)
    city: str | None = Field(default=None, max_length=100)

    # Vehicle preferences
    preferred_fuel: str = "Any"
    preferred_vehicle_type: str = "Any"
    maximum_budget: float | None = Field(default=None, gt=0)
    preferred_transmission: str = "Any"
    main_purpose: str = "Other"
    preferred_brands: str = Field(default="", max_length=500)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    date_of_birth: date | None = None
    phone_number: str | None = None
    country: str
    city: str | None = None
    preferred_fuel: str
    preferred_vehicle_type: str
    maximum_budget: float | None = None
    preferred_transmission: str
    main_purpose: str
    preferred_brands: str
    is_active: bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserUpdate(BaseModel):
    # Keep these required for compatibility with the existing profile form.
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr

    # Optional profile fields
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    date_of_birth: date | None = None
    phone_number: str | None = Field(default=None, max_length=30)
    country: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    preferred_fuel: str | None = None
    preferred_vehicle_type: str | None = None
    maximum_budget: float | None = Field(default=None, gt=0)
    preferred_transmission: str | None = None
    main_purpose: str | None = None
    preferred_brands: str | None = Field(default=None, max_length=500)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

