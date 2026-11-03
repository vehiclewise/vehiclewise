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
    ]
    for column in text_columns:
        if column in df.columns:
            df[column] = df[column].fillna("Unknown").astype(str).str.strip()
    # Convert numeric fields safely
    numeric_columns = [
        "price_eur",
        "power_hp",
        "torque_nm",
        "acceleration_0_100_s",
        "top_speed_kmh",
        "fuel_consumption_l_100km",
        "weight_kg",
        "model_year",
    ]
    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    # Keep records with identifiable makes and models
    df = df[
        df["brand"].ne("")
        & df["model"].ne("")
        & df["brand"].ne("Unknown")
        & df["model"].ne("Unknown")
    ].copy()
    # Create a display name for the existing interface
    df["Vehicle"] = df["brand"] + " " + df["model"]
    # The dataset has no confirmed prices for most vehicles.
    # Missing prices must remain missing, not become zero.
    return df.reset_index(drop=True)