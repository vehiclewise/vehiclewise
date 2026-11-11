"""Standalone Streamlit entry point for Member 4 dashboard features."""

import hashlib
import json
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PARENT_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
for candidate in (PROJECT_ROOT, PARENT_DIR):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

import pandas as pd
import streamlit as st

from member4_dashboard import user_features
from member4_dashboard.dashboard import render_dashboard
from vehicle_data import load_vehicles


st.set_page_config(page_title="VehicleWise | My Dashboard", layout="wide")
st.title("VehicleWise")
st.subheader("Your vehicle shortlist")

st.sidebar.header("Dashboard profile")
profile_input = st.sidebar.text_input("Profile ID", value="guest").strip()
st.sidebar.caption("Local demo profile; connect an authenticated user ID for shared login.")
profile_id = str(st.session_state.get("user_id") or profile_input)
if not profile_id:
    st.error("Enter a profile ID to open the dashboard.")
    st.stop()


@st.cache_data
def get_vehicles():
    return load_vehicles()


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
    fields = [
        "brand", "model", "model_year", "engine", "body_type",
        "fuel_type", "power_hp",
    ]
    identity = [
        None if pd.isna(row.get(field)) else str(row.get(field)).strip().casefold()
        for field in fields
    ]
    serialized = json.dumps(identity, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


vehicles = get_vehicles().copy()
vehicles["Vehicle"] = vehicles["brand"] + " " + vehicles["model"]
vehicles["fuel_display"] = vehicles["fuel_type"].replace(
    {"Gasoline": "Petrol", "gasoline": "Petrol"}
)

vehicles_tab, compare_tab, dashboard_tab = st.tabs(
    ["Vehicles", "Compare", "My dashboard"]
)

with vehicles_tab:
    search_text = st.text_input("Search brand or model", key="member4_search")
    search_stamp = (profile_id, search_text)
    if search_text and search_stamp != st.session_state.get("last_member4_search"):
        user_features.record_search(profile_id, search_text)
    st.session_state["last_member4_search"] = search_stamp

    filtered_vehicles = vehicles
    if search_text:
        matches = (
            filtered_vehicles["brand"].str.contains(search_text, case=False, na=False)
            | filtered_vehicles["model"].str.contains(search_text, case=False, na=False)
        )
        filtered_vehicles = filtered_vehicles[matches]

    display_fields = [
        field for field in [
            "brand", "model", "model_year", "body_type", "fuel_display",
            "power_hp", "transmission",
        ]
        if field in filtered_vehicles.columns
    ]
    st.dataframe(
        filtered_vehicles[display_fields].head(100),
        width="stretch",
        hide_index=True,
    )

    if filtered_vehicles.empty:
        st.info("No vehicles match this search.")
    else:
        vehicle_names = filtered_vehicles["Vehicle"].drop_duplicates().tolist()
        selected_name = st.selectbox("Vehicle details", vehicle_names)
        selected_rows = filtered_vehicles[
            filtered_vehicles["Vehicle"] == selected_name
        ]
        selected_vehicle = selected_rows.iloc[0]
        st.write(
            f"{selected_vehicle.get('model_year', 'Year unknown')} · "
            f"{selected_vehicle.get('fuel_display', 'Fuel unknown')} · "
            f"{selected_vehicle.get('power_hp', 'Power unknown')} hp"
        )
        if st.button("Add bookmark", key="member4_add_bookmark"):
            user_features.add_bookmark(
                profile_id,
                vehicle_key(selected_vehicle),
                selected_name,
                vehicle_record(selected_vehicle),
            )
            st.success("Vehicle added to your bookmarks.")

with compare_tab:
    st.header("Compare and save")
    comparison_source = filtered_vehicles
    comparison_names = sorted(comparison_source["Vehicle"].drop_duplicates().tolist())
    selected_names = st.multiselect(
        "Choose two or three vehicles",
        comparison_names,
        max_selections=3,
        key="member4_comparison",
    )
    if len(selected_names) >= 2:
        selected_records = [
            vehicle_record(
                comparison_source[comparison_source["Vehicle"] == name].iloc[0]
            )
            for name in selected_names
        ]
        comparison_fields = [
            ("Model year", "model_year"),
            ("Body type", "body_type"),
            ("Fuel type", "fuel_display"),
            ("Power (hp)", "power_hp"),
            ("Transmission", "transmission"),
            ("Drivetrain", "drivetrain"),
        ]
        comparison_rows = []
        for label, field in comparison_fields:
            comparison_row = {"Specification": label}
            for vehicle in selected_records:
                value = vehicle.get(field)
                comparison_row[vehicle["Vehicle"]] = (
                    "Not available" if value is None else str(value)
                )
            comparison_rows.append(comparison_row)
        st.dataframe(pd.DataFrame(comparison_rows), width="stretch", hide_index=True)
        if st.button("Save comparison", key="member4_save_comparison"):
            user_features.save_comparison(profile_id, selected_records)
            st.success("Comparison saved to your dashboard.")
    else:
        st.info("Select at least two vehicles to compare.")

with dashboard_tab:
    render_dashboard(profile_id)
