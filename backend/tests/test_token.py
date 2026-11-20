import pytest

from backend.auth.token import create_access_token, verify_access_token


def test_create_access_token_without_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(
        RuntimeError,
        match="SECRET_KEY is not configured.",
    ):
        create_access_token(1)


def test_verify_access_token_without_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(
        RuntimeError,
        match="SECRET_KEY is not configured.",
    ):
        verify_access_token("invalid.token.value")
