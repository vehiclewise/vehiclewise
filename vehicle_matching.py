from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).parent

CATALOGUE_FILE = BASE_DIR / "german_vehicle_catalogue.csv"
SPECS_FILE = BASE_DIR / "vehicle_specs_database_cleaned.csv"
ALIASES_FILE = BASE_DIR / "vehicle_model_aliases.csv"


def normalize_key(make, model):
    """Create a consistent key for matching vehicle names."""
    return (
        f"{str(make).strip().casefold()}|"
        f"{str(model).strip().casefold()}"
    )


def load_vehicle_matching():
    """Match catalogue vehicles with available technical specifications."""

    catalogue = pd.read_csv(CATALOGUE_FILE)
    specs = pd.read_csv(SPECS_FILE)
    aliases = pd.read_csv(ALIASES_FILE)

    specs["match_key"] = [
        normalize_key(make, model)
        for make, model in zip(specs["make"], specs["model"])
    ]

    exact_keys = set(specs["match_key"])

    alias_map = {}

    for _, row in aliases.iterrows():
        if str(row["reviewed"]).strip().casefold() not in {
            "true", "1", "yes"
        }:
            continue

        source = normalize_key(
            row["catalogue_brand"],
            row["catalogue_model"],
        )

        target = normalize_key(
            row["specs_make"],
            row["specs_model"],
        )

        if target not in exact_keys:
            raise ValueError(
                f"Alias target does not exist in specs database: {target}"
            )

        if source in exact_keys:
            raise ValueError(
                f"Alias conflicts with an exact match: {source}"
            )

        if source in alias_map and alias_map[source] != target:
            raise ValueError(
                f"Conflicting aliases found for: {source}"
            )

        alias_map[source] = target

    catalogue["match_key"] = [
        normalize_key(brand, model)
        for brand, model in zip(
            catalogue["brand"],
            catalogue["model"],
        )
    ]

    catalogue["spec_match_key"] = catalogue["match_key"]
    catalogue["match_type"] = "unmatched"

    exact_mask = catalogue["match_key"].isin(exact_keys)

    catalogue.loc[exact_mask, "match_type"] = "exact"

    alias_mask = (
        ~exact_mask
        & catalogue["match_key"].isin(alias_map)
    )

    catalogue.loc[alias_mask, "match_type"] = "alias"

    catalogue.loc[alias_mask, "spec_match_key"] = (
        catalogue.loc[alias_mask, "match_key"].map(alias_map)
    )

    return catalogue, specs


def get_spec_variants(catalogue_vehicle, specs):
    """Return every specification variant for one catalogue vehicle."""

    match_key = catalogue_vehicle["spec_match_key"]

    return specs[
        specs["match_key"] == match_key
    ].drop(columns=["match_key"]).copy()
