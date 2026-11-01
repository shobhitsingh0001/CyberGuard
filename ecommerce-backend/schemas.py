import re
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime


# --- User Schemas ---
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    mobile_number: str
    password: str

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("Enter your full name")
        return v

    @field_validator("mobile_number")
    @classmethod
    def clean_mobile(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
        if not re.fullmatch(r"[6-9]\d{9}", digits):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return digits

    @field_validator("password")
    @classmethod
    def strong_enough(cls, v: str) -> str:
        if len(v) < 8 or not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("Password must be at least 8 characters and include a letter and a number")
        return v


class UserLogin(BaseModel):
    email_or_mobile: str
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    mobile_number: str
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LoginActivityResponse(BaseModel):
    id: int
    success: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Product Schemas ---
class ProductCreate(BaseModel):
    name: str
    category: str
    icon: Optional[str] = None
    image_url: Optional[str] = None
    price: float
    quantity: int


class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    icon: Optional[str] = None
    image_url: Optional[str] = None
    price: float
    quantity: int

    class Config:
        from_attributes = True


# --- Order Schemas ---
class OrderItemCreate(BaseModel):
    product_id: int
    name: str
    image_url: Optional[str] = None
    price: float


class OrderCreate(BaseModel):
    items: List[OrderItemCreate]


class OrderStatusUpdate(BaseModel):
    status: str


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    name: str
    image_url: Optional[str] = None
    price: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    order_code: str
    total: float
    status: str
    created_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True
