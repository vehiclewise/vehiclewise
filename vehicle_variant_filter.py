import pandas as pd


def filter_vehicle_variants(
    variants,
    model_year=None,
    fuel_type=None,
    min_power=None,
    max_power=None,
    transmission=None,
):
    """Filter vehicle specification variants without modifying the original data."""

    results = variants.copy()

    if model_year is not None:
        results = results[
            (results["gen_year_start"].isna()
             | (results["gen_year_start"] <= model_year))
            & (results["gen_year_end"].isna()
               | (results["gen_year_end"] >= model_year))
        ]

    if fuel_type:
        results = results[
            results["fuel_type"].str.contains(
                fuel_type, case=False, na=False
            )
        ]

    if min_power is not None:
        results = results[results["power_hp"] >= min_power]

    if max_power is not None:
        results = results[results["power_hp"] <= max_power]

    if transmission:
        results = results[
            results["transmission"].str.contains(
                transmission, case=False, na=False
            )
        ]

    return results.reset_index(drop=True)
