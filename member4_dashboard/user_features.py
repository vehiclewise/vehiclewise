"""SQLite persistence for bookmarks, searches, and saved comparisons."""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("user_features.sqlite3")


@contextmanager
def _connection(database_path=None):
    connection = sqlite3.connect(database_path or DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS bookmarks (
                profile_id TEXT NOT NULL,
                vehicle_key TEXT NOT NULL,
                vehicle_name TEXT NOT NULL,
                vehicle_data TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (profile_id, vehicle_key)
            );
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT NOT NULL,
                query TEXT NOT NULL,
                searched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS saved_comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id TEXT NOT NULL,
                vehicle_names TEXT NOT NULL,
                vehicle_data TEXT NOT NULL,
                saved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _profile(profile_id):
    profile_id = str(profile_id).strip()
    if not profile_id:
        raise ValueError("A profile ID is required.")
    return profile_id


def add_bookmark(profile_id, vehicle_key, vehicle_name, vehicle_data):
    with _connection() as connection:
        connection.execute(
            """INSERT INTO bookmarks
               (profile_id, vehicle_key, vehicle_name, vehicle_data)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(profile_id, vehicle_key) DO UPDATE SET
                   vehicle_name = excluded.vehicle_name,
                   vehicle_data = excluded.vehicle_data,
                   updated_at = CURRENT_TIMESTAMP""",
            (
                _profile(profile_id),
                vehicle_key,
                vehicle_name,
                json.dumps(vehicle_data, default=str),
            ),
        )


def list_bookmarks(profile_id):
    with _connection() as connection:
        rows = connection.execute(
            "SELECT * FROM bookmarks WHERE profile_id = ? ORDER BY updated_at DESC",
            (_profile(profile_id),),
        ).fetchall()
    return [
        {**dict(row), "vehicle_data": json.loads(row["vehicle_data"])}
        for row in rows
    ]


def update_bookmark_note(profile_id, vehicle_key, note):
    with _connection() as connection:
        cursor = connection.execute(
            """UPDATE bookmarks SET note = ?, updated_at = CURRENT_TIMESTAMP
               WHERE profile_id = ? AND vehicle_key = ?""",
            (str(note), _profile(profile_id), vehicle_key),
        )
    return cursor.rowcount > 0


def delete_bookmark(profile_id, vehicle_key):
    with _connection() as connection:
        cursor = connection.execute(
            "DELETE FROM bookmarks WHERE profile_id = ? AND vehicle_key = ?",
            (_profile(profile_id), vehicle_key),
        )
    return cursor.rowcount > 0


def record_search(profile_id, query):
    query = str(query).strip()
    if not query:
        return
    with _connection() as connection:
        connection.execute(
            "INSERT INTO search_history (profile_id, query) VALUES (?, ?)",
            (_profile(profile_id), query),
        )


def list_search_history(profile_id):
    with _connection() as connection:
        rows = connection.execute(
            "SELECT * FROM search_history WHERE profile_id = ? ORDER BY id DESC",
            (_profile(profile_id),),
        ).fetchall()
    return [dict(row) for row in rows]


def delete_search(profile_id, search_id):
    with _connection() as connection:
        cursor = connection.execute(
            "DELETE FROM search_history WHERE profile_id = ? AND id = ?",
            (_profile(profile_id), search_id),
        )
    return cursor.rowcount > 0


def clear_search_history(profile_id):
    with _connection() as connection:
        connection.execute(
            "DELETE FROM search_history WHERE profile_id = ?",
            (_profile(profile_id),),
        )


def save_comparison(profile_id, vehicle_data):
    names = [vehicle["Vehicle"] for vehicle in vehicle_data]
    with _connection() as connection:
        cursor = connection.execute(
            """INSERT INTO saved_comparisons
               (profile_id, vehicle_names, vehicle_data) VALUES (?, ?, ?)""",
            (
                _profile(profile_id),
                json.dumps(names),
                json.dumps(vehicle_data, default=str),
            ),
        )
    return cursor.lastrowid


def list_saved_comparisons(profile_id):
    with _connection() as connection:
        rows = connection.execute(
            """SELECT * FROM saved_comparisons
               WHERE profile_id = ? ORDER BY id DESC""",
            (_profile(profile_id),),
        ).fetchall()
    return [
        {
            **dict(row),
            "vehicle_names": json.loads(row["vehicle_names"]),
            "vehicle_data": json.loads(row["vehicle_data"]),
        }
        for row in rows
    ]


def delete_comparison(profile_id, comparison_id):
    with _connection() as connection:
        cursor = connection.execute(
            "DELETE FROM saved_comparisons WHERE profile_id = ? AND id = ?",
            (_profile(profile_id), comparison_id),
        )
    return cursor.rowcount > 0
