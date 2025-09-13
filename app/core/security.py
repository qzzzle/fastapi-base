# app/core/security.py
"""
Portable security primitives
- Provide password hashing and JWT helpers.
- Keep types/claims generic so app-layer can decide the schema.
"""

from datetime import datetime, timedelta, timezone
from typing import Sequence, Tuple

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from app.core.config import configs

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
bearer = HTTPBearer(auto_error=False)  # we’ll raise our own 401 with clearer messages


def get_password_hash(password: str) -> str:
    """Hash a plain password."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: dict, expires_delta: timedelta | None = None) -> Tuple[str, str]:
    """
    Create a JWT.
    - subject: dict of claims you want to store (e.g., {"sub": user_id, "roles": [...]})
    - returns (token, human_readable_expiry)
    """
    expire = datetime.now(tz=timezone.utc) + (expires_delta or timedelta(minutes=configs.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"exp": expire, **subject}
    token = jwt.encode(payload, configs.SECRET_KEY, algorithm=ALGORITHM)
    return token, expire.isoformat()


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT.
    - Raises for invalid/expired tokens.
    - Keep minimal and generic on purpose.
    """
    try:
        return jwt.decode(token, configs.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


class JWTBearer(HTTPBearer):
    """
    FastAPI dependency to extract & validate Bearer tokens.
    Returns the raw token string for app-layer to decode/authorize.
    """

    async def __call__(self, request):
        credentials: HTTPAuthorizationCredentials | None = await super().__call__(request)
        if not credentials or credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication scheme")
        # Only basic presence/shape check here; detailed decode happens where you need it.
        return credentials.credentials
