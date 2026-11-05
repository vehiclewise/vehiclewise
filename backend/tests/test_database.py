from unittest.mock import MagicMock

import pytest

from backend.database import connection


def test_get_db_returns_database_session(monkeypatch):
    mock_db = MagicMock()

    monkeypatch.setattr(
        connection,
        "SessionLocal",
        lambda: mock_db,
    )

    db_generator = connection.get_db()

    db = next(db_generator)

    assert db is mock_db

    with pytest.raises(StopIteration):
        next(db_generator)

    mock_db.close.assert_called_once()


def test_get_db_closes_session_after_exception(monkeypatch):
    mock_db = MagicMock()

    monkeypatch.setattr(
        connection,
        "SessionLocal",
        lambda: mock_db,
    )

    db_generator = connection.get_db()

    db = next(db_generator)

    assert db is mock_db

    db_generator.close()

    mock_db.close.assert_called_once()
