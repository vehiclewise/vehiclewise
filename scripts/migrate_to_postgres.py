import os
from pathlib import Path

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from backend.database.connection import Base
from backend.auth.models import User, PasswordResetToken


BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_DB = BASE_DIR / "vehiclewise.db"


def migrate():
    target_url = os.getenv("DATABASE_URL", "").strip()

    if not target_url:
        raise RuntimeError("DATABASE_URL is not configured.")

    if target_url.startswith("postgres://"):
        target_url = target_url.replace("postgres://", "postgresql://", 1)

    if not target_url.startswith("postgresql://"):
        raise RuntimeError("Target DATABASE_URL must point to PostgreSQL.")

    if not SOURCE_DB.exists():
        raise RuntimeError(f"Source database not found: {SOURCE_DB}")

    source_engine = create_engine(f"sqlite:///{SOURCE_DB}")
    target_engine = create_engine(target_url)

    try:
        SourceSession = sessionmaker(bind=source_engine)
        TargetSession = sessionmaker(bind=target_engine)

        with SourceSession() as source:
            users = source.scalars(select(User).order_by(User.id)).all()
            tokens = source.scalars(
                select(PasswordResetToken).order_by(PasswordResetToken.id)
            ).all()

            user_data = [
                {
                    column.name: getattr(user, column.name)
                    for column in User.__table__.columns
                }
                for user in users
            ]

            token_data = [
                {
                    column.name: getattr(token, column.name)
                    for column in PasswordResetToken.__table__.columns
                }
                for token in tokens
            ]

        print(f"Source records: {len(user_data)} users, {len(token_data)} reset records.")

        # Create only the authentication tables in the destination.
        Base.metadata.create_all(
            bind=target_engine,
            tables=[User.__table__, PasswordResetToken.__table__],
        )

        with target_engine.begin() as connection:
            existing_users = connection.execute(
                select(func.count()).select_from(User.__table__)
            ).scalar_one()

            existing_tokens = connection.execute(
                select(func.count()).select_from(PasswordResetToken.__table__)
            ).scalar_one()

            if existing_users or existing_tokens:
                raise RuntimeError(
                    "Destination authentication tables are not empty. "
                    "Migration stopped to avoid overwriting existing records."
                )

            if user_data:
                connection.execute(User.__table__.insert(), user_data)

            if token_data:
                connection.execute(PasswordResetToken.__table__.insert(), token_data)

            copied_users = connection.execute(
                select(func.count()).select_from(User.__table__)
            ).scalar_one()

            copied_tokens = connection.execute(
                select(func.count()).select_from(PasswordResetToken.__table__)
            ).scalar_one()

            if copied_users != len(user_data) or copied_tokens != len(token_data):
                raise RuntimeError("Record-count verification failed.")

            # Keep PostgreSQL generated IDs above the imported IDs.
            connection.exec_driver_sql(
                """
                SELECT setval(
                    pg_get_serial_sequence('users', 'id'),
                    COALESCE((SELECT MAX(id) FROM users), 1),
                    (SELECT MAX(id) IS NOT NULL FROM users)
                )
                """
            )
            connection.exec_driver_sql(
                """
                SELECT setval(
                    pg_get_serial_sequence('password_reset_tokens', 'id'),
                    COALESCE((SELECT MAX(id) FROM password_reset_tokens), 1),
                    (SELECT MAX(id) IS NOT NULL FROM password_reset_tokens)
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
