import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
import jwt

from app.auth import get_current_user


@pytest.fixture
def valid_token():
    payload = {
        "sub": "user-123",
        "aud": "authenticated",
        "iss": "https://example.supabase.co/auth/v1",
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")
    return token


def test_get_current_user_missing_header():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(authorization=None)
    assert exc_info.value.status_code == 401
    assert "Missing" in exc_info.value.detail


def test_get_current_user_malformed_header():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(authorization="InvalidToken")
    assert exc_info.value.status_code == 401


def test_get_current_user_bearer_typo():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(authorization="Beaer token123")
    assert exc_info.value.status_code == 401


@patch("app.auth._jwks_client")
def test_get_current_user_expired_token(mock_jwks_client):
    mock_jwks_client.get_signing_key_from_jwt.return_value = MagicMock(key="key")

    with patch("jwt.decode") as mock_decode:
        mock_decode.side_effect = jwt.ExpiredSignatureError()

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(authorization="Bearer token123")

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()


@patch("app.auth._jwks_client")
def test_get_current_user_invalid_token(mock_jwks_client):
    mock_jwks_client.get_signing_key_from_jwt.return_value = MagicMock(key="key")

    with patch("jwt.decode") as mock_decode:
        mock_decode.side_effect = jwt.InvalidTokenError("Bad token")

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(authorization="Bearer badtoken")

        assert exc_info.value.status_code == 401


@patch("app.auth._jwks_client")
def test_get_current_user_missing_sub(mock_jwks_client):
    mock_jwks_client.get_signing_key_from_jwt.return_value = MagicMock(key="key")

    with patch("jwt.decode") as mock_decode:
        mock_decode.return_value = {"aud": "authenticated"}

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(authorization="Bearer token123")

        assert exc_info.value.status_code == 401
        assert "sub" in exc_info.value.detail.lower()


@patch("app.auth._jwks_client")
def test_get_current_user_valid(mock_jwks_client):
    mock_jwks_client.get_signing_key_from_jwt.return_value = MagicMock(key="key")

    with patch("jwt.decode") as mock_decode:
        mock_decode.return_value = {"sub": "user-456", "aud": "authenticated"}

        result = get_current_user(authorization="Bearer validtoken")

    assert result == "user-456"
