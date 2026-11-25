from pathlib import Path
import pandas as pd

DATA_FILE = Path(__file__).parent / "vehiclewise_vehicle_data.csv"


def load_vehicles():
    """Load vehicle specifications from the CSV database."""

    df = pd.read_csv(DATA_FILE)

    # Standardise text fields
    text_columns = [
        "brand",
        "model",
        "vehicle_type",
        "body_type",
        "fuel_type",
        "transmission",
        "drivetrain",
        "engine"
    ]

    for column in text_columns:
        if column in df.columns:
            df[column] = (
                df[column]
                .fillna("Unknown")
                .astype(str)
                .str.strip()
            )

    # Convert numeric fields
    numeric_columns = [
        "price_eur",
        "power_hp",
        "torque_nm",
        "acceleration_0_100_s",
        "top_speed_kmh",
        "fuel_consumption_l_100km",
        "weight_kg",
        "model_year",
        "year_start"
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column], errors="coerce"
            )

    # Use year_start if model_year is missing
    if "model_year" in df.columns and "year_start" in df.columns:
        df["model_year"] = df["model_year"].fillna(
            df["year_start"]
        )

    # Keep valid vehicle records
    df = df[
        df["brand"].notna()
        & df["model"].notna()
        & df["brand"].ne("")
        & df["model"].ne("")
        & df["brand"].ne("Unknown")
        & df["model"].ne("Unknown")
    ].copy()

    # Create vehicle display name
    df["Vehicle"] = df["brand"] + " " + df["model"]

    # Keep missing prices as missing
    return df.reset_index(drop=True)