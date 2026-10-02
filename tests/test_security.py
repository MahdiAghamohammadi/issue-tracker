from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.config import get_settings
from app.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hashing() -> None:
    hashed = hash_password("strong-password")

    assert hashed != "strong-password"
    assert verify_password("strong-password", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_round_trip() -> None:
    token = create_access_token("user-id")

    assert decode_access_token(token) == "user-id"


def test_expired_token_is_rejected() -> None:
    settings = get_settings()
    token = jwt.encode(
        {"sub": "user-id", "exp": datetime.now(UTC) - timedelta(seconds=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_token_without_subject_is_rejected() -> None:
    settings = get_settings()
    token = jwt.encode(
        {"exp": datetime.now(UTC) + timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)
