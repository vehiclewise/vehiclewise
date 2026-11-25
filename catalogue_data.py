from pathlib import Path
import pandas as pd

DATA_FILE = Path(__file__).parent / "german_vehicle_catalogue.csv"


def load_catalogue():
    """Load and clean the German-market vehicle catalogue."""
    df = pd.read_csv(DATA_FILE)

    text_columns = [
        "vehicle_type",
        "brand",
        "model",
        "body_type",
        "countries",
        "regions",
        "fuel_type",
        "transmission",
        "availability_status",
        "price_source",
        "official_source_url",
        "record_scope",
    ]

    for column in text_columns:
        if column in df.columns:
            df[column] = df[column].fillna("").astype(str).str.strip()

    numeric_columns = ["model_year", "power_hp", "price_eur"]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df[
        df["brand"].ne("")
        & df["model"].ne("")
    ].copy()

    df["Vehicle"] = df["brand"] + " " + df["model"]

    return df.reset_index(drop=True)
