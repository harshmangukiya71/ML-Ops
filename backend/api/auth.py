"""
Auth API — JWT-based register / login / me.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.database.models import Token, TokenData, UserCreate, UserOut
from backend.database.mongo import users_col

logger  = logging.getLogger(__name__)
router  = APIRouter()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SECRET_KEY  = os.getenv("JWT_SECRET", "changeme-in-production")
ALGORITHM   = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MIN  = int(os.getenv("JWT_EXPIRE_MINUTES", "10080"))

pwd_ctx     = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2      = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def _create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire  = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=EXPIRE_MIN)
    )
    payload["exp"] = expire
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2)) -> UserOut:
    """FastAPI dependency — resolves JWT → user."""
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise cred_exc
    except JWTError:
        raise cred_exc

    doc = await users_col().find_one({"_id": ObjectId(user_id)})
    if not doc:
        raise cred_exc

    return UserOut(
        id=str(doc["_id"]),
        email=doc["email"],
        created_at=doc["created_at"],
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate):
    """Create a new user account."""
    existing = await users_col().find_one({"email": payload.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    doc = {
        "email":         payload.email,
        "password_hash": _hash_password(payload.password),
        "created_at":    datetime.now(timezone.utc),
    }
    result = await users_col().insert_one(doc)
    token  = _create_token({"sub": str(result.inserted_id)})
    logger.info("User registered: %s", payload.email)
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    """Authenticate and return JWT."""
    doc = await users_col().find_one({"email": form.username})
    if not doc or not _verify_password(form.password, doc["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    token = _create_token({"sub": str(doc["_id"])})
    logger.info("User login: %s", form.username)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user: UserOut = Depends(get_current_user)):
    """Return current user info."""
    return user
