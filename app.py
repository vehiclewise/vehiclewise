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
from member4_dashboard import user_features
from member4_dashboard.dashboard import render_dashboard
from vehicle_data import load_vehicles

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="VehicleWise",
    page_icon="🚗",
    layout="wide"
)

st.sidebar.subheader("Dashboard profile")
profile_input = st.sidebar.text_input("Profile ID", value="guest").strip()
st.sidebar.caption("Local demo profile unless an authenticated user ID is available.")
profile_id = str(st.session_state.get("user_id") or profile_input)
if not profile_id:
    st.sidebar.error("Enter a profile ID to use dashboard features.")
    st.stop()

# --------------------------------------------------
# LOAD DATABASE
# --------------------------------------------------

@st.cache_data
def get_data():
    return load_vehicles()

df = get_data().copy()

# Standardise text values for display and filtering
for column in ["brand", "model", "vehicle_type", "body_type",
                "fuel_type", "transmission", "drivetrain"]:
    if column in df.columns:
        df[column] = df[column].fillna("Unknown").astype(str).str.strip()
        df[column] = df[column].replace("", "Unknown")

df["Vehicle"] = df["brand"] + " " + df["model"]

# Normalise fuel labels for display
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
st.subheader("Compare vehicles and discover the right one for you")
st.write(
    "Explore vehicle specifications, compare models, and receive "
    "recommendations based on your preferences."
)

st.info(
    "Database note: This dataset contains historical and recent vehicle "
    "variants from multiple markets. It does not confirm current availability "
    "in Germany. Prices are not yet available in the database."
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

fuel_options = sorted(df["fuel_display"].dropna().unique().tolist())
selected_fuels = st.sidebar.multiselect(
    "Fuel type",
    fuel_options,
    default=[]
)

body_options = sorted(df["body_type"].dropna().unique().tolist())
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
        filtered_df["brand"].str.contains(search_text, case=False, na=False)
        | filtered_df["model"].str.contains(search_text, case=False, na=False)
    )
    filtered_df = filtered_df[search_mask]

if selected_brands:
    filtered_df = filtered_df[filtered_df["brand"].isin(selected_brands)]

if selected_fuels:
    filtered_df = filtered_df[filtered_df["fuel_display"].isin(selected_fuels)]

if selected_bodies:
    filtered_df = filtered_df[filtered_df["body_type"].isin(selected_bodies)]

# --------------------------------------------------
# DATABASE OVERVIEW
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

col1.metric("Vehicle variants", f"{len(df):,}")
col2.metric("Brands", f"{df['brand'].nunique():,}")
col3.metric("Matching variants", f"{len(filtered_df):,}")

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


def vehicle_details(row):
    details = {
        "Brand": row.get("brand", "Unknown"),
        "Model": row.get("model", "Unknown"),
        "Vehicle type": row.get("vehicle_type", "Unknown"),
        "Body type": row.get("body_type", "Unknown"),
        "Model year": display_value(row.get("model_year")),
        "Fuel type": row.get("fuel_display", "Unknown"),
        "Power": display_value(row.get("power_hp"), " hp"),
        "Torque": display_value(row.get("torque_nm"), " Nm"),
        "Transmission": row.get("transmission", "Unknown"),
        "Drivetrain": row.get("drivetrain", "Unknown"),
        "0–100 km/h": display_value(row.get("acceleration_0_100_s"), " seconds"),
        "Top speed": display_value(row.get("top_speed_kmh"), " km/h"),
        "Fuel consumption": display_value(
            row.get("fuel_consumption_l_100km"), " L/100 km"
        ),
        "Weight": display_value(row.get("weight_kg"), " kg"),
        "Price in Germany": "Not available"
    }
    return details


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
        "brand", "model", "model_year", "engine", "body_type",
        "fuel_type", "power_hp",
    ]
    identity = [
        None if pd.isna(row.get(field)) else str(row.get(field)).strip().casefold()
        for field in key_fields
    ]
    encoded = json.dumps(identity, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

# --------------------------------------------------
# TAB 1: EXPLORE
# --------------------------------------------------

with tab1:
    st.header("Explore Vehicles")
    st.write("Search and filter the database to find vehicle variants.")

    if filtered_df.empty:
        st.warning("No vehicles match your filters. Try changing your search.")
    else:
        display_columns = [
            "brand", "model", "model_year", "body_type",
            "fuel_display", "power_hp", "transmission"
        ]
        display_columns = [
            column for column in display_columns
            if column in filtered_df.columns
        ]

        st.dataframe(
            filtered_df[display_columns].rename(columns={
                "brand": "Brand",
                "model": "Model",
                "model_year": "Model Year",
                "body_type": "Body Type",
                "fuel_display": "Fuel Type",
                "power_hp": "Power (hp)",
                "transmission": "Transmission"
            }),
            width="stretch",
            hide_index=True
        )

        vehicle_options = filtered_df["Vehicle"].drop_duplicates().tolist()
        chosen_vehicle = st.selectbox(
            "View vehicle details",
            vehicle_options,
            key="explore_vehicle"
        )

        matching_rows = filtered_df[filtered_df["Vehicle"] == chosen_vehicle]

        if not matching_rows.empty:
            row = matching_rows.iloc[0]
            st.subheader(chosen_vehicle)

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

# --------------------------------------------------
# TAB 2: COMPARE
# --------------------------------------------------

with tab2:
    st.header("Compare Vehicles")
    st.write("Select two or three vehicles to compare their specifications.")

    compare_source = filtered_df if not filtered_df.empty else df
    compare_options = sorted(compare_source["Vehicle"].drop_duplicates().tolist())

    selected_comparison = st.multiselect(
        "Choose vehicles",
        compare_options,
        max_selections=3,
        key="comparison"
    )

    if len(selected_comparison) >= 2:
        comparison_rows = []

        comparison_fields = [
            ("Brand", "brand"),
            ("Model", "model"),
            ("Model year", "model_year"),
            ("Body type", "body_type"),
            ("Fuel type", "fuel_display"),
            ("Power (hp)", "power_hp"),
            ("Torque (Nm)", "torque_nm"),
            ("Transmission", "transmission"),
            ("Drivetrain", "drivetrain"),
            ("0–100 km/h (seconds)", "acceleration_0_100_s"),
            ("Top speed (km/h)", "top_speed_kmh"),
            ("Fuel consumption (L/100 km)", "fuel_consumption_l_100km"),
            ("Weight (kg)", "weight_kg")
        ]

        for label, column in comparison_fields:
            comparison_row = {"Specification": label}

            for vehicle in selected_comparison:
                vehicle_rows = compare_source[
                    compare_source["Vehicle"] == vehicle
                ]

                value = vehicle_rows.iloc[0].get(column, None)

                if pd.isna(value) or value is None:
                    comparison_row[vehicle] = "Not available"
                else:
                    comparison_row[vehicle] = str(value)

            comparison_rows.append(comparison_row)

        comparison_table = pd.DataFrame(comparison_rows)
        st.dataframe(comparison_table, width="stretch", hide_index=True)

        comparison_records = [
            vehicle_record(
                compare_source[compare_source["Vehicle"] == vehicle].iloc[0]
            )
            for vehicle in selected_comparison
        ]
        if st.button("Save comparison", key="save_dashboard_comparison"):
            user_features.save_comparison(profile_id, comparison_records)
            st.success("Comparison saved to your dashboard.")

        st.caption(
            "Comparisons use the first matching variant for each selected "
            "brand and model. Check the model year and engine before drawing "
            "conclusions."
        )

    else:
        st.info("Select at least two vehicles to compare.")

# --------------------------------------------------
# TAB 3: CATALOGUE
# --------------------------------------------------

with tab3:
    st.header("Vehicle Catalogue")
    st.write("Browse the available vehicle records in the database.")

    st.write(f"**{len(filtered_df):,} variants found**")

    catalogue_columns = [
        "Vehicle", "model_year", "vehicle_type", "body_type",
        "fuel_display", "power_hp", "transmission"
    ]
    catalogue_columns = [
        column for column in catalogue_columns
        if column in filtered_df.columns
    ]

    if filtered_df.empty:
        st.warning("No vehicles match the current filters.")
    else:
        st.dataframe(
            filtered_df[catalogue_columns].rename(columns={
                "model_year": "Model Year",
                "vehicle_type": "Vehicle Type",
                "body_type": "Body Type",
                "fuel_display": "Fuel Type",
                "power_hp": "Power (hp)",
                "transmission": "Transmission"
            }),
            width="stretch",
            hide_index=True
        )

        csv_data = filtered_df[catalogue_columns].to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Download filtered catalogue as CSV",
            data=csv_data,
            file_name="vehiclewise_catalogue.csv",
            mime="text/csv"
        )

# --------------------------------------------------
# TAB 4: RECOMMENDATIONS
# --------------------------------------------------

with tab4:
    st.header("Personalised Vehicle Recommendations")
    st.write("Tell us what matters to you and explore matching vehicles.")

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
            & (
                recommendations["fuel_consumption_l_100km"]
                <= maximum_consumption
            )
        ]

    recommendations = recommendations.drop_duplicates(
        subset=["brand", "model", "model_year", "engine"]
    )

    st.write(f"**{len(recommendations):,} matching variants**")

    if recommendations.empty:
        st.warning("No vehicles match these preferences. Try relaxing a filter.")
    else:
        recommendation_columns = [
            "Vehicle", "model_year", "body_type", "fuel_display",
            "power_hp", "fuel_consumption_l_100km", "transmission"
        ]
        recommendation_columns = [
            column for column in recommendation_columns
            if column in recommendations.columns
        ]

        st.dataframe(
            recommendations[recommendation_columns].head(100).rename(columns={
                "model_year": "Model Year",
                "body_type": "Body Type",
                "fuel_display": "Fuel Type",
                "power_hp": "Power (hp)",
                "fuel_consumption_l_100km": "Fuel Consumption (L/100 km)",
                "transmission": "Transmission"
            }),
            width="stretch",
            hide_index=True
        )

        st.caption(
            "These recommendations match technical preferences only. "
            "Budget-based recommendations will be added after reliable "
            "German-market price data is collected."
        )

# --------------------------------------------------
# TAB 5: USER DASHBOARD
# --------------------------------------------------

with tab5:
    render_dashboard(profile_id)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()
st.caption(
    "VehicleWise | Academic software engineering project | "
    "Specifications are compiled from a dataset and may need verification. "
    "Current German availability and prices are not guaranteed."
)