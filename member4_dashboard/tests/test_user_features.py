import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.auth.models import User
from backend.database.connection import Base
from member4_dashboard import user_features


@pytest.fixture
def dashboard_database(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(bind=engine)
    monkeypatch.setattr(user_features, "SessionLocal", test_session)

    with test_session() as session:
        session.add(
            User(
                username="dashboard-test",
                email="dashboard-test@example.com",
                hashed_password="not-a-real-password",
            )
        )
        session.commit()

    yield

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_save_comparison_persists_named_vehicles(dashboard_database):
    vehicles = [
        {"Vehicle": "BMW 3 Series", "power_hp": 255},
        {"Vehicle": "Audi A4", "power_hp": 201},
    ]

    comparison_id = user_features.save_comparison("1", vehicles)

    saved_comparisons = user_features.list_saved_comparisons("1")
    assert len(saved_comparisons) == 1
    assert saved_comparisons[0]["id"] == comparison_id
    assert saved_comparisons[0]["profile_id"] == "1"
    assert saved_comparisons[0]["vehicle_names"] == ["BMW 3 Series", "Audi A4"]
    assert saved_comparisons[0]["vehicle_data"] == vehicles
    assert saved_comparisons[0]["saved_at"] is not None


@pytest.mark.parametrize(
    "vehicle_data",
    [
        [],
        [{"Vehicle": "BMW 3 Series"}],
        [
            {"Vehicle": "BMW 3 Series"},
            {"Vehicle": "Audi A4"},
            {"Vehicle": "Mercedes C-Class"},
            {"Vehicle": "Volvo S60"},
        ],
        [{"power_hp": 255}, {"Vehicle": "Audi A4"}],
        [{"Vehicle": " "}, {"Vehicle": "Audi A4"}],
        ["BMW 3 Series", {"Vehicle": "Audi A4"}],
    ],
)
def test_save_comparison_rejects_invalid_vehicle_lists(
    dashboard_database, vehicle_data
):
    with pytest.raises(ValueError):
        user_features.save_comparison("1", vehicle_data)

    assert user_features.list_saved_comparisons("1") == []
