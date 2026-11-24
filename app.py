import hashlib
import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
for candidate in (PROJECT_ROOT, PARENT_DIR):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from member4_dashboard import user_features
from member4_dashboard.dashboard import render_dashboard
from vehicle_data import load_vehicles
from catalogue_data import load_catalogue
from auth_ui import require_authentication


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="VehicleWise",
    page_icon="🚗",
    layout="wide"
)


# --------------------------------------------------
# USER AUTHENTICATION
# --------------------------------------------------

user = require_authentication()
profile_id = str(user["id"])


# --------------------------------------------------
# LOAD VEHICLE DATABASE
# --------------------------------------------------

@st.cache_data
def get_data():
    return load_vehicles()


@st.cache_data
def get_catalogue_data():
    return load_catalogue()


df = get_data().copy()

catalogue_df = get_catalogue_data().copy()


# Standardise text values
for column in [
    "brand",
    "model",
    "vehicle_type",
    "body_type",
    "fuel_type",
    "transmission",
    "drivetrain"
]:
    if column in df.columns:
        df[column] = (
            df[column]
            .fillna("Unknown")
            .astype(str)
            .str.strip()
        )
        df[column] = df[column].replace("", "Unknown")


df["Vehicle"] = df["brand"] + " " + df["model"]


# Normalise fuel labels
df["fuel_display"] = df["fuel_type"].replace({
    "Gasoline": "Petrol",
    "gasoline": "Petrol",
    "Diesel": "Diesel",
    "Electric": "Electric",
    "Hybrid": "Hybrid"
})


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🚗 VehicleWise")

st.subheader(
    "Compare vehicles and discover the right one for you"
)

st.write(
    f"Welcome, **{user['username']}**! "
    "Explore vehicle specifications, compare models, "
    "and receive recommendations based on your preferences."
)

st.info(
    "Database note: This dataset contains historical and recent "
    "vehicle variants from multiple markets. It does not confirm "
    "current availability in Germany. Prices are not yet available "
    "in the database."
)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.header("🔎 Find Your Vehicle")

search_text = st.sidebar.text_input(
    "Search brand or model",
    placeholder="e.g. BMW, Toyota, Golf"
)

search_stamp = (profile_id, search_text)
if search_text and search_stamp != st.session_state.get("last_dashboard_search"):
    user_features.record_search(profile_id, search_text)
st.session_state["last_dashboard_search"] = search_stamp

brands = sorted(df["brand"].dropna().unique().tolist())

selected_brands = st.sidebar.multiselect(
    "Brand",
    brands,
    default=[]
)

fuel_options = sorted(
    df["fuel_display"].dropna().unique().tolist()
)

selected_fuels = st.sidebar.multiselect(
    "Fuel type",
    fuel_options,
    default=[]
)

body_options = sorted(
    df["body_type"].dropna().unique().tolist()
)

selected_bodies = st.sidebar.multiselect(
    "Body type",
    body_options,
    default=[]
)


# --------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------

filtered_df = df.copy()

if search_text:
    search_mask = (
        filtered_df["brand"].str.contains(
            search_text,
            case=False,
            na=False
        )
        |
        filtered_df["model"].str.contains(
            search_text,
            case=False,
            na=False
        )
    )

    filtered_df = filtered_df[search_mask]


if selected_brands:
    filtered_df = filtered_df[
        filtered_df["brand"].isin(selected_brands)
    ]


if selected_fuels:
    filtered_df = filtered_df[
        filtered_df["fuel_display"].isin(selected_fuels)
    ]


if selected_bodies:
    filtered_df = filtered_df[
        filtered_df["body_type"].isin(selected_bodies)
    ]


# --------------------------------------------------
# DATABASE OVERVIEW
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

col1.metric(
    "Vehicle variants",
    f"{len(df):,}"
)

col2.metric(
    "Brands",
    f"{df['brand'].nunique():,}"
)

col3.metric(
    "Matching variants",
    f"{len(filtered_df):,}"
)

st.divider()


# --------------------------------------------------
# NAVIGATION
# --------------------------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Explore",
    "⚖️ Compare",
    "📚 Catalogue",
    "🎯 Recommendations",
    "👤 My dashboard"
])


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def display_value(value, suffix=""):
    if pd.isna(value) or str(value).strip() == "":
        return "Not available"
    return f"{value}{suffix}"


def production_period(row):
    start = row.get("year_start")
    end = row.get("year_end")

    if pd.notna(start) and pd.notna(end):
        return f"{int(start)}–{int(end)}"
    if pd.notna(start):
        return f"From {int(start)}"
    if pd.notna(end):
        return f"Until {int(end)}"
    return "Not available"


def vehicle_details(row):
    return {
        "Brand": row.get("brand", "Unknown"),
        "Model": row.get("model", "Unknown"),
        "Generation": row.get("generation", "Not available"),
        "Production period": production_period(row),
        "Vehicle type": row.get("vehicle_type", "Unknown"),
        "Body type": row.get("body_type", "Unknown"),
        "Fuel type": row.get("fuel_display", "Unknown"),
        "Power": display_value(row.get("power_hp"), " hp"),
        "Torque": display_value(row.get("torque_nm"), " Nm"),
        "Transmission": row.get("transmission", "Unknown"),
        "Drivetrain": row.get("drivetrain", "Unknown"),
        "0–100 km/h": display_value(row.get("acceleration_0_100_s"), " seconds"),
        "Top speed": display_value(row.get("top_speed_kmh"), " km/h"),
        "Fuel consumption": display_value(row.get("fuel_consumption_l_100km"), " L/100 km"),
        "Weight": display_value(row.get("weight_kg"), " kg"),
        "Price in Germany": display_value(row.get("price_eur"), " €"),
    }


def vehicle_record(row):
    record = {}
    for key, value in row.to_dict().items():
        if pd.isna(value):
            record[str(key)] = None
        elif hasattr(value, "item"):
            record[str(key)] = value.item()
        else:
            record[str(key)] = value
    return record


def vehicle_key(row):
    key_fields = [
        "brand", "model", "generation", "year_start", "year_end",
        "engine", "body_type", "fuel_type", "power_hp", "transmission",
    ]
    identity = [
        None if pd.isna(row.get(field)) else str(row.get(field)).strip().casefold()
        for field in key_fields
    ]
    encoded = json.dumps(identity, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


# TAB 1: EXPLORE
# --------------------------------------------------

with tab1:

    st.header("Explore Vehicles")
    st.write(
        "Search and filter the database. Select a vehicle row "
        "to view its specifications."
    )

    if filtered_df.empty:
        st.warning("No vehicles match your filters. Try changing your search.")

    else:
        explore_table = filtered_df.copy().reset_index(drop=True)

        explore_table["Production Period"] = explore_table.apply(
            production_period, axis=1
        )

        # Match available German catalogue prices by brand and model.
        price_data = catalogue_df.dropna(
            subset=["price_eur"]
        ).copy()

        price_data["_brand_key"] = (
            price_data["brand"].astype(str).str.strip().str.casefold()
        )
        price_data["_model_key"] = (
            price_data["model"].astype(str).str.strip().str.casefold()
        )

        price_lookup = (
            price_data.groupby(["_brand_key", "_model_key"])["price_eur"]
            .min()
            .to_dict()
        )

        explore_table["_brand_key"] = (
            explore_table["brand"].astype(str).str.strip().str.casefold()
        )
        explore_table["_model_key"] = (
            explore_table["model"].astype(str).str.strip().str.casefold()
        )

        explore_table["Starting Price (€)"] = explore_table.apply(
            lambda row: (
                f"€{price_lookup[(row['_brand_key'], row['_model_key'])]:,.2f}"
                if (row["_brand_key"], row["_model_key"]) in price_lookup
                else "Not available"
            ),
            axis=1,
        )

        explore_table = explore_table.drop(
            columns=["_brand_key", "_model_key"],
        )

        explore_table["__vehicle_key"] = explore_table.apply(
            vehicle_key, axis=1
        )

        display_columns = [
            "brand",
            "model",
            "Production Period",
            "Starting Price (€)",
            "body_type",
            "fuel_display",
            "power_hp",
            "transmission",
            "__vehicle_key",
        ]

        display_columns = [
            column for column in display_columns
            if column in explore_table.columns
        ]

        explore_table = explore_table[display_columns].rename(
            columns={
                "brand": "Brand",
                "model": "Model",
                "body_type": "Body Type",
                "fuel_display": "Fuel Type",
                "power_hp": "Power (hp)",
                "transmission": "Transmission",
            }
        )

        grid_builder = GridOptionsBuilder.from_dataframe(explore_table)

        grid_builder.configure_default_column(
            resizable=True,
            sortable=True,
            filterable=True,
            editable=False,
        )

        grid_builder.configure_selection(
            selection_mode="single",
            use_checkbox=False,
        )

        grid_builder.configure_column("__vehicle_key", hide=True)

        grid_builder.configure_grid_options(
            rowSelection="single",
            suppressRowClickSelection=False,
            animateRows=True,
            rowHeight=40,
            headerHeight=45,
        )

        grid_response = AgGrid(
            explore_table,
            gridOptions=grid_builder.build(),
            update_on=["selectionChanged"],
            fit_columns_on_grid_load=True,
            height=450,
            theme="streamlit",
            allow_unsafe_jscode=False,
            key="explore_vehicle_grid",
        )

        selected_rows = grid_response.get("selected_rows")
        selected_row = None

        if selected_rows is not None:
            if isinstance(selected_rows, pd.DataFrame):
                if not selected_rows.empty:
                    selected_row = selected_rows.iloc[0]
            elif isinstance(selected_rows, list) and selected_rows:
                selected_row = selected_rows[0]

        if selected_row is not None:
            selected_key = selected_row.get("__vehicle_key")

            matching_rows = filtered_df[
                filtered_df.apply(
                    lambda row: vehicle_key(row) == selected_key,
                    axis=1,
                )
            ]

            if not matching_rows.empty:
                row = matching_rows.iloc[0]
                chosen_vehicle = f"{row['brand']} {row['model']}"

                st.divider()
                st.subheader(f"Vehicle Details: {chosen_vehicle}")

                details = vehicle_details(row)
                detail_cols = st.columns(3)

                for index, (label, value) in enumerate(details.items()):
                    with detail_cols[index % 3]:
                        st.write(f"**{label}:** {value}")

                if st.button("Add bookmark", key="add_dashboard_bookmark"):
                    user_features.add_bookmark(
                        profile_id,
                        vehicle_key(row),
                        chosen_vehicle,
                        vehicle_record(row),
                    )
                    st.success("Vehicle added to your dashboard bookmarks.")

        else:
            st.info(
                "Select a vehicle row above to view its full specifications."
            )


# TAB 2: COMPARE
# --------------------------------------------------

with tab2:

    st.header("Compare Vehicles")
    st.write(
        "Select two or three models, then choose the exact variant "
        "you want to compare."
    )

    compare_source = filtered_df if not filtered_df.empty else df

    compare_options = sorted(
        compare_source["Vehicle"].drop_duplicates().tolist()
    )

    selected_comparison = st.multiselect(
        "Choose vehicle models",
        compare_options,
        max_selections=3,
        key="comparison"
    )

    if len(selected_comparison) >= 2:

        selected_variants = []

        for vehicle_number, vehicle in enumerate(selected_comparison, start=1):
            vehicle_rows = compare_source[
                compare_source["Vehicle"] == vehicle
            ].copy().reset_index(drop=True)

            vehicle_rows["_variant_label"] = vehicle_rows.apply(
                lambda row: " | ".join([
                    str(row.get("generation"))
                    if pd.notna(row.get("generation")) else "Generation unknown",
                    str(int(row["model_year"]))
                    if pd.notna(row.get("model_year")) else "Year unknown",
                    str(row.get("engine"))
                    if pd.notna(row.get("engine")) else "Engine unknown",
                    str(row.get("fuel_display", "Fuel unknown")),
                    f"{row['power_hp']:g} hp"
                    if pd.notna(row.get("power_hp")) else "Power unknown",
                    str(row.get("transmission"))
                    if pd.notna(row.get("transmission")) else "Transmission unknown",
                    f"Variant {row.name + 1}",
                ]),
                axis=1,
            )

            st.markdown(f"**{vehicle_number}. {vehicle}**")

            selected_label = st.selectbox(
                f"Choose variant for {vehicle}",
                vehicle_rows["_variant_label"].tolist(),
                key=f"comparison_variant_{vehicle_number}",
            )

            selected_row = vehicle_rows[
                vehicle_rows["_variant_label"] == selected_label
            ].iloc[0]

            selected_variants.append(selected_row)

        comparison_fields = [
            ("Brand", "brand"),
            ("Model", "model"),
            ("Generation", "generation"),
            ("Model year", "model_year"),
            ("Engine", "engine"),
            ("Body type", "body_type"),
            ("Fuel type", "fuel_display"),
            ("Power (hp)", "power_hp"),
            ("Torque (Nm)", "torque_nm"),
            ("Transmission", "transmission"),
            ("Drivetrain", "drivetrain"),
            ("0–100 km/h (seconds)", "acceleration_0_100_s"),
            ("Top speed (km/h)", "top_speed_kmh"),
            ("Fuel consumption (L/100 km)", "fuel_consumption_l_100km"),
            ("Weight (kg)", "weight_kg"),
            ("Price (€)", "price_eur"),
        ]

        comparison_rows = []

        for label, column in comparison_fields:
            comparison_row = {"Specification": label}

            for vehicle, row in zip(selected_comparison, selected_variants):
                value = row.get(column)

                if pd.isna(value) or value is None:
                    comparison_row[vehicle] = "Not available"
                else:
                    comparison_row[vehicle] = str(value)

            comparison_rows.append(comparison_row)

        st.subheader("Comparison Results")
        st.dataframe(
            pd.DataFrame(comparison_rows),
            width="stretch",
            hide_index=True,
        )

        comparison_records = [
            vehicle_record(row.drop(labels=["_variant_label"], errors="ignore"))
            for row in selected_variants
        ]

        if st.button("Save comparison", key="save_dashboard_comparison"):
            user_features.save_comparison(profile_id, comparison_records)
            st.success("Comparison saved to your dashboard.")

        st.caption(
            "Each vehicle is compared using the exact variant selected above. "
            "Some specifications may be unavailable in the database."
        )

    else:
        st.info("Select at least two vehicle models to compare.")


# --------------------------------------------------

# TAB 3: CATALOGUE
# --------------------------------------------------

with tab3:
    st.header("📚 German Vehicle Catalogue")
    st.write(
        "Explore vehicles listed in the German-market catalogue. "
        "Prices and specifications are shown only where available."
    )

    catalogue = catalogue_df.copy()

    catalogue_search = st.text_input(
        "Search brand or model",
        placeholder="e.g. BMW, Toyota, Golf",
        key="catalogue_search"
    )

    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        vehicle_types = sorted(catalogue["vehicle_type"].dropna().unique().tolist())
        selected_types = st.multiselect(
            "Vehicle type",
            vehicle_types,
            default=vehicle_types,
            key="catalogue_vehicle_type"
        )

    with filter_col2:
        catalogue_brands = sorted(catalogue["brand"].dropna().unique().tolist())
        selected_catalogue_brands = st.multiselect(
            "Brand",
            catalogue_brands,
            key="catalogue_brand"
        )

    with filter_col3:
        fuel_types = sorted(catalogue["fuel_type"].dropna().unique().tolist())
        selected_catalogue_fuels = st.multiselect(
            "Fuel type",
            fuel_types,
            key="catalogue_fuel"
        )

    if catalogue_search:
        search_mask = (
            catalogue["brand"].str.contains(catalogue_search, case=False, na=False)
            | catalogue["model"].str.contains(catalogue_search, case=False, na=False)
        )
        catalogue = catalogue[search_mask]

    if selected_types:
        catalogue = catalogue[catalogue["vehicle_type"].isin(selected_types)]
    else:
        catalogue = catalogue.iloc[0:0]

    if selected_catalogue_brands:
        catalogue = catalogue[catalogue["brand"].isin(selected_catalogue_brands)]

    if selected_catalogue_fuels:
        catalogue = catalogue[catalogue["fuel_type"].isin(selected_catalogue_fuels)]

    metric1, metric2, metric3 = st.columns(3)
    metric1.metric("Matching vehicles", f"{len(catalogue):,}")
    metric2.metric("Brands", f"{catalogue['brand'].nunique():,}")
    metric3.metric(
        "Vehicles with prices",
        f"{catalogue['price_eur'].notna().sum():,}"
    )

    st.divider()

    if catalogue.empty:
        st.warning("No vehicles match your selected filters.")
    else:
        display_catalogue = catalogue[
            [
                "vehicle_type", "brand", "model", "body_type",
                "model_year", "fuel_type", "power_hp", "transmission",
                "price_eur", "availability_status", "last_verified"
            ]
        ].copy()

        display_catalogue["price_eur"] = display_catalogue["price_eur"].apply(
            lambda price: f"€{price:,.2f}" if pd.notna(price) else "Not available"
        )

        display_catalogue = display_catalogue.rename(columns={
            "vehicle_type": "Vehicle Type",
            "brand": "Brand",
            "model": "Model",
            "body_type": "Body Type",
            "model_year": "Model Year",
            "fuel_type": "Fuel Type",
            "power_hp": "Power (hp)",
            "transmission": "Transmission",
            "price_eur": "Starting Price",
            "availability_status": "Availability in Germany",
            "last_verified": "Last Verified"
        })

        st.dataframe(
            display_catalogue,
            width="stretch",
            hide_index=True
        )

        csv_data = catalogue.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download filtered German catalogue",
            data=csv_data,
            file_name="vehiclewise_german_catalogue.csv",
            mime="text/csv"
        )

        st.caption(
            "Starting prices may be promotional and can change. "
            "Always verify prices and availability with the manufacturer."
        )

        st.divider()
        st.subheader("🚘 Vehicle Details")

        vehicle_options = catalogue["Vehicle"].drop_duplicates().tolist()
        selected_vehicle = st.selectbox(
            "Select a vehicle to view its specifications",
            vehicle_options,
            key="catalogue_selected_vehicle"
        )

        selected_vehicle_data = catalogue[
            catalogue["Vehicle"] == selected_vehicle
        ].iloc[0]

        detail_col1, detail_col2 = st.columns(2)

        with detail_col1:
            st.markdown("### General Information")
            st.write("**Brand:**", selected_vehicle_data["brand"])
            st.write("**Model:**", selected_vehicle_data["model"])
            st.write("**Vehicle Type:**", selected_vehicle_data["vehicle_type"])
            st.write("**Body Type:**", selected_vehicle_data["body_type"])
            st.write("**Model Year:**", display_value(selected_vehicle_data["model_year"]))
            st.write("**Fuel Type:**", selected_vehicle_data["fuel_type"])

        with detail_col2:
            st.markdown("### Specifications")
            st.write("**Power:**", display_value(selected_vehicle_data["power_hp"], " hp"))
            st.write("**Transmission:**", display_value(selected_vehicle_data["transmission"]))
            st.write("**Starting Price:**", display_value(selected_vehicle_data["price_eur"], " €"))
            st.write("**Availability:**", selected_vehicle_data["availability_status"])
            st.write("**Last Verified:**", selected_vehicle_data["last_verified"])

        st.markdown("### Price Information")
        st.write("**Price Source:**", selected_vehicle_data["price_source"])

        if selected_vehicle_data["official_source_url"]:
            st.link_button(
                "Visit Official Manufacturer Website",
                selected_vehicle_data["official_source_url"]
            )


# TAB 4: RECOMMENDATIONS
# --------------------------------------------------

with tab4:

    st.header("Personalised Vehicle Recommendations")

    st.write(
        "Choose your preferences and select a vehicle "
        "to view its details and save it."
    )

    preference_col1, preference_col2 = st.columns(2)

    with preference_col1:

        preferred_fuel = st.selectbox(
            "Preferred fuel type",
            ["Any"] + fuel_options,
            key="recommendation_fuel"
        )

        minimum_power = st.number_input(
            "Minimum power (hp)",
            min_value=0,
            max_value=2000,
            value=0,
            step=25
        )

    with preference_col2:

        preferred_body = st.selectbox(
            "Preferred body type",
            ["Any"] + body_options,
            key="recommendation_body"
        )

        maximum_consumption = st.number_input(
            "Maximum fuel consumption (L/100 km; 0 = no limit)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.5
        )

    recommendations = df.copy()

    if preferred_fuel != "Any":
        recommendations = recommendations[
            recommendations["fuel_display"] == preferred_fuel
        ]

    if preferred_body != "Any":
        recommendations = recommendations[
            recommendations["body_type"] == preferred_body
        ]

    if minimum_power > 0:
        recommendations = recommendations[
            recommendations["power_hp"].fillna(0) >= minimum_power
        ]

    if maximum_consumption > 0:
        recommendations = recommendations[
            recommendations["fuel_consumption_l_100km"].notna()
            &
            (
                recommendations["fuel_consumption_l_100km"]
                <= maximum_consumption
            )
        ]

    recommendations = recommendations.drop_duplicates(
        subset=["brand", "model", "model_year", "engine"]
    ).head(100).reset_index(drop=True)

    st.write(f"**{len(recommendations):,} matching variants**")

    if recommendations.empty:

        st.warning(
            "No vehicles match these preferences. "
            "Try relaxing a filter."
        )

    else:

        recommendation_table = recommendations.copy()

        recommendation_table["Production Period"] = (
            recommendation_table.apply(production_period, axis=1)
        )

        price_data = catalogue_df.dropna(
            subset=["price_eur"]
        ).copy()

        price_data["_brand_key"] = (
            price_data["brand"].astype(str).str.strip().str.casefold()
        )

        price_data["_model_key"] = (
            price_data["model"].astype(str).str.strip().str.casefold()
        )

        price_lookup = (
            price_data.groupby(["_brand_key", "_model_key"])["price_eur"]
            .min()
            .to_dict()
        )

        recommendation_table["_brand_key"] = (
            recommendation_table["brand"]
            .astype(str).str.strip().str.casefold()
        )

        recommendation_table["_model_key"] = (
            recommendation_table["model"]
            .astype(str).str.strip().str.casefold()
        )

        recommendation_table["Starting Price (€)"] = (
            recommendation_table.apply(
                lambda row: (
                    f"€{price_lookup[(row['_brand_key'], row['_model_key'])]:,.2f}"
                    if (row["_brand_key"], row["_model_key"]) in price_lookup
                    else "Not available"
                ),
                axis=1,
            )
        )

        recommendation_table = recommendation_table.drop(
            columns=["_brand_key", "_model_key"]
        )

        recommendation_table["__vehicle_key"] = (
            recommendation_table.apply(vehicle_key, axis=1)
        )

        display_columns = [
            "brand",
            "model",
            "Production Period",
            "Starting Price (€)",
            "body_type",
            "fuel_display",
            "power_hp",
            "transmission",
            "__vehicle_key",
        ]

        display_columns = [
            column for column in display_columns
            if column in recommendation_table.columns
        ]

        recommendation_table = recommendation_table[
            display_columns
        ].rename(
            columns={
                "brand": "Brand",
                "model": "Model",
                "body_type": "Body Type",
                "fuel_display": "Fuel Type",
                "power_hp": "Power (hp)",
                "transmission": "Transmission",
            }
        )

        grid_builder = GridOptionsBuilder.from_dataframe(
            recommendation_table
        )

        grid_builder.configure_default_column(
            resizable=True,
            sortable=True,
            filterable=True,
            editable=False,
        )

        grid_builder.configure_selection(
            selection_mode="single",
            use_checkbox=False,
        )

        grid_builder.configure_column("__vehicle_key", hide=True)

        grid_builder.configure_grid_options(
            rowSelection="single",
            suppressRowClickSelection=False,
            animateRows=True,
            rowHeight=40,
            headerHeight=45,
        )

        grid_response = AgGrid(
            recommendation_table,
            gridOptions=grid_builder.build(),
            update_on=["selectionChanged"],
            fit_columns_on_grid_load=True,
            height=450,
            theme="streamlit",
            allow_unsafe_jscode=False,
            key="recommendation_vehicle_grid",
        )

        selected_rows = grid_response.get("selected_rows")
        selected_row = None

        if selected_rows is not None:
            if isinstance(selected_rows, pd.DataFrame):
                if not selected_rows.empty:
                    selected_row = selected_rows.iloc[0]

            elif isinstance(selected_rows, list) and selected_rows:
                selected_row = selected_rows[0]

        if selected_row is not None:

            selected_key = selected_row.get("__vehicle_key")

            matching_rows = recommendations[
                recommendations.apply(
                    lambda row: vehicle_key(row) == selected_key,
                    axis=1,
                )
            ]

            if not matching_rows.empty:

                row = matching_rows.iloc[0]
                chosen_vehicle = f"{row['brand']} {row['model']}"

                st.divider()
                st.subheader(f"Vehicle Details: {chosen_vehicle}")

                details = vehicle_details(row)
                detail_cols = st.columns(3)

                for index, (label, value) in enumerate(details.items()):
                    with detail_cols[index % 3]:
                        st.write(f"**{label}:** {value}")

                try:
                    saved_bookmarks = user_features.list_bookmarks(
                        profile_id
                    )

                    saved_keys = {
                        item["vehicle_key"]
                        for item in saved_bookmarks
                    }

                    if vehicle_key(row) in saved_keys:
                        st.info("This vehicle is already in your bookmarks.")

                    elif st.button(
                        "Add bookmark",
                        key="add_recommendation_bookmark"
                    ):
                        user_features.add_bookmark(
                            profile_id,
                            vehicle_key(row),
                            chosen_vehicle,
                            vehicle_record(row),
                        )

                        st.success(
                            "Vehicle added to your dashboard bookmarks."
                        )

                        st.rerun()

                except Exception as error:
                    st.error("Could not access your bookmarks.")
                    print(f"Bookmark error: {error}")

        else:
            st.info(
                "Select a vehicle row to view its specifications "
                "and add it to your bookmarks."
            )

        st.caption(
            "Prices are shown where reliable German-market data is available. "
            "Missing prices are marked as Not available. "
            "Always verify prices with the manufacturer."
        )


# TAB 5: USER DASHBOARD
# --------------------------------------------------

with tab5:
    render_dashboard(profile_id)


# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "VehicleWise | Academic software engineering project | "
    "Specifications are compiled from a dataset and may need verification. "
    "Current German availability and prices are not guaranteed."
)
