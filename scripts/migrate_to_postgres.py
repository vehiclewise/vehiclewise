import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, select, func

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

from backend.database.connection import Base
from backend.auth.models import User, PasswordResetToken

SOURCE_DB = BASE_DIR / "vehiclewise.db"


def migrate():
    target_url = os.getenv("DATABASE_URL", "").strip()

    if not target_url:
        raise RuntimeError("DATABASE_URL is not configured.")

    if target_url.startswith("postgres://"):
        target_url = target_url.replace(
            "postgres://", "postgresql://", 1
        )

    if target_url.startswith("postgresql://"):
        target_url = target_url.replace(
            "postgresql://", "postgresql+psycopg2://", 1
        )

    if not target_url.startswith("postgresql+psycopg2://"):
        raise RuntimeError("Target DATABASE_URL must point to PostgreSQL.")

    if not SOURCE_DB.exists():
        raise RuntimeError(f"Source database not found: {SOURCE_DB}")

    source_engine = create_engine(f"sqlite:///{SOURCE_DB}")
    target_engine = create_engine(target_url, pool_pre_ping=True)

    try:
        with source_engine.connect() as source:
            users = source.execute(
                select(User.__table__).order_by(User.id)
            ).mappings().all()

            tokens = source.execute(
                select(PasswordResetToken.__table__).order_by(
                    PasswordResetToken.id
                )
            ).mappings().all()

            user_data = [dict(row) for row in users]
            token_data = [dict(row) for row in tokens]

        print(
            f"Source records: {len(user_data)} users, "
            f"{len(token_data)} password-reset records."
        )

        # Create only the two authentication tables.
        Base.metadata.create_all(
            bind=target_engine,
            tables=[
                User.__table__,
                PasswordResetToken.__table__,
            ],
        )

        with target_engine.begin() as connection:
            existing_users = connection.execute(
                select(func.count()).select_from(User.__table__)
            ).scalar_one()

            existing_tokens = connection.execute(
                select(func.count()).select_from(
                    PasswordResetToken.__table__
                )
            ).scalar_one()

            if existing_users or existing_tokens:
                raise RuntimeError(
                    "Destination authentication tables are not empty. "
                    "Migration stopped without copying records."
                )

            if user_data:
                connection.execute(
                    User.__table__.insert(), user_data
                )

            if token_data:
                connection.execute(
                    PasswordResetToken.__table__.insert(), token_data
                )

            copied_users = connection.execute(
                select(func.count()).select_from(User.__table__)
            ).scalar_one()

            copied_tokens = connection.execute(
                select(func.count()).select_from(
                    PasswordResetToken.__table__
                )
            ).scalar_one()

            if (
                copied_users != len(user_data)
                or copied_tokens != len(token_data)
            ):
                raise RuntimeError("Record-count verification failed.")

            # Synchronize PostgreSQL ID sequences.
            for table in ("users", "password_reset_tokens"):
                connection.exec_driver_sql(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table}', 'id'),
                        COALESCE((SELECT MAX(id) FROM {table}), 1),
                        (SELECT MAX(id) IS NOT NULL FROM {table})
                    )
                    """
                )

        print("Migration completed and verified.")
        print(f"Users copied: {copied_users}")
        print(f"Password-reset records copied: {copied_tokens}")

    finally:
        source_engine.dispose()
        target_engine.dispose()


if __name__ == "__main__":
    migrate()
