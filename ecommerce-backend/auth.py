import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserSession, LoginActivity
from schemas import (
    UserRegister, UserLogin, UserResponse,
    TokenResponse, LoginActivityResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])

PBKDF2_ITERATIONS = 260_000
SESSION_DAYS = 7
MAX_FAILED_ATTEMPTS = 5
LOCK_WINDOW_SECONDS = 5


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt_hex, hash_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), hash_hex)
    except Exception:
        return False


def normalize_identifier(raw: str) -> str:
    raw = raw.strip()
    if "@" in raw:
        return raw.lower()
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    return digits


def client_info(request: Request):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent", "")[:300]
    return ip, ua


def create_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.add(UserSession(
        user_id=user.id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=SESSION_DAYS),
    ))
    return token


def get_current_user(
    authorization: str = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not signed in")
    token = authorization.split(" ", 1)[1].strip()

    session = db.query(UserSession).filter(UserSession.token == token).first()
    if not session or session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
    return session.user


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: UserRegister, request: Request, db: Session = Depends(get_db)):
    email = data.email.lower()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    if db.query(User).filter(User.mobile_number == data.mobile_number).first():
        raise HTTPException(status_code=409, detail="An account with this mobile number already exists")

    user = User(
        full_name=data.full_name,
        email=email,
        mobile_number=data.mobile_number,
        password_hash=hash_password(data.password),
        last_login_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    ip, ua = client_info(request)
    db.add(LoginActivity(
        user_id=user.id, identifier=email, success=True, ip_address=ip, user_agent=ua
    ))
    token = create_session(db, user)
    db.commit()

    return TokenResponse(access_token=token, user=user)


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, request: Request, db: Session = Depends(get_db)):
    identifier = normalize_identifier(data.email_or_mobile)
    ip, ua = client_info(request)

    window_start = datetime.utcnow() - timedelta(seconds=LOCK_WINDOW_SECONDS)
    recent_failures = db.query(LoginActivity).filter(
        LoginActivity.identifier == identifier,
        LoginActivity.success == False,  # noqa: E712
        LoginActivity.created_at >= window_start,
    ).count()
    if recent_failures >= MAX_FAILED_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed attempts. Try again in {LOCK_WINDOW_SECONDS} seconds.",
        )

    user = db.query(User).filter(
        or_(User.email == identifier, User.mobile_number == identifier)
    ).first()

    if not user or not verify_password(data.password, user.password_hash):
        db.add(LoginActivity(
            user_id=user.id if user else None,
            identifier=identifier, success=False, ip_address=ip, user_agent=ua,
        ))
        db.commit()
        raise HTTPException(status_code=401, detail="Incorrect email/mobile or password")

    user.last_login_at = datetime.utcnow()
    db.add(LoginActivity(
        user_id=user.id, identifier=identifier, success=True, ip_address=ip, user_agent=ua
    ))
    token = create_session(db, user)
    db.commit()
    db.refresh(user)

    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout")
def logout(
    authorization: str = Header(default=None),
    db: Session = Depends(get_db),
):
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        db.query(UserSession).filter(UserSession.token == token).delete()
        db.commit()
    return {"message": "Signed out"}


@router.get("/login-history", response_model=List[LoginActivityResponse])
def login_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(LoginActivity)
        .filter(LoginActivity.user_id == user.id)
        .order_by(LoginActivity.created_at.desc())
        .limit(20)
        .all()
    )
