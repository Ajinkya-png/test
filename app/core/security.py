"""
Security utilities for the Food Delivery Voice AI platform.

Implements:
- JWT token creation and verification
- Password hashing and verification
- API key validation (for internal services)
- Data encryption/decryption for PII (AES)
- Webhook signature verification (Twilio, Stripe)
- Rate limiting hooks (Redis-based, optional)
"""

import os
import jwt
import base64
import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, Header, Request, status

from .config import settings

logger = logging.getLogger(__name__)

# ============================================================
# PASSWORD HASHING
# ============================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify user password."""
    return pwd_context.verify(plain_password, hashed_password)

# ============================================================
# JWT AUTHENTICATION
# ============================================================

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day default

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str) -> dict:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def validate_api_key(x_api_key: str = Header(None)) -> None:
    """Validate static API key for internal endpoints."""
    expected = settings.INTERNAL_API_KEY
    if not x_api_key or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized API key")


# Generate Fernet key if missing
FERNET_KEY = settings.FERNET_KEY or Fernet.generate_key().decode()

fernet = Fernet(FERNET_KEY.encode() if isinstance(FERNET_KEY, str) else FERNET_KEY)

def encrypt_data(data: str) -> str:
    """Encrypt sensitive data like phone numbers or addresses."""
    if not data:
        return data
    token = fernet.encrypt(data.encode())
    return token.decode()

def decrypt_data(token: str) -> str:
    """Decrypt previously encrypted data."""
    if not token:
        return token
    try:
        return fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        logger.warning("Decryption failed (invalid token)")
        return token

# ============================================================
# WEBHOOK SIGNATURE VERIFICATION (Twilio / Stripe)
# ============================================================

def verify_webhook_signature(request: Request, signature_header: str, secret: str) -> bool:
    """
    Verify webhook signatures (generic HMAC-based).
    For example: Stripe or Twilio webhooks.
    """
    payload = request.body()
    computed_sig = hmac.new(
        key=secret.encode(),
        msg=payload if isinstance(payload, bytes) else str(payload).encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature_header, computed_sig):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")
    return True

# ============================================================
# RATE LIMITING (Optional, Redis-based)
# ============================================================

import time
import redis

def check_rate_limit(client_id: str, limit: int = 30, period: int = 60):
    """
    Simple token bucket rate limiter using Redis.
    client_id: unique identifier (e.g., IP or user ID)
    limit: max requests allowed per period
    """
    try:
        r = redis.from_url(settings.REDIS_URL)
        key = f"ratelimit:{client_id}"
        current = r.get(key)
        if current and int(current) >= limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        pipe = r.pipeline()
        pipe.incr(key, 1)
        pipe.expire(key, period)
        pipe.execute()
    except Exception as e:
        logger.warning(f"Rate limiting failed: {e}")
        pass  # Fail open (don’t block requests if Redis down)

# ============================================================
# REQUEST AUTHENTICATION DEPENDENCIES
# ============================================================

from fastapi import Depends

async def get_current_user(token: str = Header(None)) -> Dict[str, Any]:
    """FastAPI dependency to fetch user info from JWT."""
    if not token:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    payload = verify_access_token(token)
    return payload

async def protected_route(token: str = Header(None)):
    """Dependency for secure endpoints."""
    verify_access_token(token)
    return True

# ============================================================
# DATA ANONYMIZATION HELPERS
# ============================================================

def anonymize_phone(phone: str) -> str:
    """Mask phone number for logs or analytics."""
    if not phone or len(phone) < 4:
        return "****"
    return f"{'*' * (len(phone) - 4)}{phone[-4:]}"

def anonymize_email(email: str) -> str:
    """Mask email address for logs."""
    if not email or "@" not in email:
        return "****"
    name, domain = email.split("@")
    return f"{name[0]}***@{domain}"

# ============================================================
# END OF FILE
# ============================================================
