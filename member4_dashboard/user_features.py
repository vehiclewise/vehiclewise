"""SQLAlchemy persistence for bookmarks, searches, and saved comparisons."""

import json

from backend.auth.models import User  # Register the users table
from backend.database.connection import SessionLocal
from member4_dashboard.models import Bookmark, SearchHistory, SavedComparison


def _profile(profile_id):
    value = str(profile_id).strip()
    if not value:
        raise ValueError("A profile ID is required.")

    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError("The profile ID must be a valid user ID.") from None


def _timestamp(value):
    return value.isoformat() if value else None


def add_bookmark(profile_id, vehicle_key, vehicle_name, vehicle_data):
    with SessionLocal() as session:
        bookmark = (
            session.query(Bookmark)
            .filter_by(
                profile_id=_profile(profile_id),
                vehicle_key=vehicle_key,
            )
            .first()
        )

        if bookmark is None:
            bookmark = Bookmark(
                profile_id=_profile(profile_id),
                vehicle_key=vehicle_key,
                vehicle_name=vehicle_name,
                vehicle_data=json.dumps(vehicle_data, default=str),
                note="",
            )
            session.add(bookmark)
        else:
            bookmark.vehicle_name = vehicle_name
            bookmark.vehicle_data = json.dumps(vehicle_data, default=str)

        session.commit()


def list_bookmarks(profile_id):
    with SessionLocal() as session:
        rows = (
            session.query(Bookmark)
            .filter_by(profile_id=_profile(profile_id))
            .order_by(Bookmark.updated_at.desc())
            .all()
        )

        return [
            {
                "id": row.id,
                "profile_id": str(row.profile_id),
                "vehicle_key": row.vehicle_key,
                "vehicle_name": row.vehicle_name,
                "vehicle_data": json.loads(row.vehicle_data),
                "note": row.note,
                "updated_at": _timestamp(row.updated_at),
            }
            for row in rows
        ]


def update_bookmark_note(profile_id, vehicle_key, note):
    with SessionLocal() as session:
        bookmark = (
            session.query(Bookmark)
            .filter_by(
                profile_id=_profile(profile_id),
                vehicle_key=vehicle_key,
            )
            .first()
        )

        if bookmark is None:
            return False

        bookmark.note = str(note)
        session.commit()
        return True


def delete_bookmark(profile_id, vehicle_key):
    with SessionLocal() as session:
        bookmark = (
            session.query(Bookmark)
            .filter_by(
                profile_id=_profile(profile_id),
                vehicle_key=vehicle_key,
            )
            .first()
        )

        if bookmark is None:
            return False

        session.delete(bookmark)
        session.commit()
        return True


def record_search(profile_id, query):
    query = str(query).strip()
    if not query:
        return

    with SessionLocal() as session:
        session.add(
            SearchHistory(
                profile_id=_profile(profile_id),
                query=query,
            )
        )
        session.commit()


def list_search_history(profile_id):
    with SessionLocal() as session:
        rows = (
            session.query(SearchHistory)
            .filter_by(profile_id=_profile(profile_id))
            .order_by(SearchHistory.id.desc())
            .all()
        )

        return [
            {
                "id": row.id,
                "profile_id": str(row.profile_id),
                "query": row.query,
                "searched_at": _timestamp(row.searched_at),
            }
            for row in rows
        ]


def delete_search(profile_id, search_id):
    with SessionLocal() as session:
        row = (
            session.query(SearchHistory)
            .filter_by(
                profile_id=_profile(profile_id),
                id=search_id,
            )
            .first()
        )

        if row is None:
            return False

        session.delete(row)
        session.commit()
        return True


def clear_search_history(profile_id):
    with SessionLocal() as session:
        (
            session.query(SearchHistory)
            .filter_by(profile_id=_profile(profile_id))
            .delete(synchronize_session=False)
        )
        session.commit()


def save_comparison(profile_id, vehicle_data):
    names = [vehicle["Vehicle"] for vehicle in vehicle_data]

    with SessionLocal() as session:
        comparison = SavedComparison(
            profile_id=_profile(profile_id),
            vehicle_names=json.dumps(names),
            vehicle_data=json.dumps(vehicle_data, default=str),
        )
        session.add(comparison)
        session.commit()
        session.refresh(comparison)
        return comparison.id


def list_saved_comparisons(profile_id):
    with SessionLocal() as session:
        rows = (
            session.query(SavedComparison)
            .filter_by(profile_id=_profile(profile_id))
            .order_by(SavedComparison.id.desc())
            .all()
        )

        return [
            {
                "id": row.id,
                "profile_id": str(row.profile_id),
                "vehicle_names": json.loads(row.vehicle_names),
                "vehicle_data": json.loads(row.vehicle_data),
                "saved_at": _timestamp(row.saved_at),
            }
            for row in rows
        ]


def delete_comparison(profile_id, comparison_id):
    with SessionLocal() as session:
        comparison = (
            session.query(SavedComparison)
            .filter_by(
                profile_id=_profile(profile_id),
                id=comparison_id,
            )
            .first()
        )

        if comparison is None:
            return False

        session.delete(comparison)
        session.commit()
        return True
