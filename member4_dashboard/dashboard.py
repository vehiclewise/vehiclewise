"""Dashboard UI for saved user vehicle activity."""

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


def render_dashboard(profile_id):
    bookmarks = user_features.list_bookmarks(profile_id)
    searches = user_features.list_search_history(profile_id)
    comparisons = user_features.list_saved_comparisons(profile_id)
    feedback_key = f"bookmark_feedback_{profile_id}"
    feedback = st.session_state.pop(feedback_key, None)
    if feedback is not None:
        feedback_type, message = feedback
        if feedback_type == "success":
            st.success(message)
        else:
            st.warning(message)

    st.header("My dashboard")
    st.caption("Your bookmarks, recent searches, and saved comparisons.")

    bookmark_metric, search_metric, comparison_metric = st.columns(3)
    bookmark_metric.metric("Bookmarks", len(bookmarks))
    search_metric.metric("Searches", len(searches))
    comparison_metric.metric("Saved comparisons", len(comparisons))

    bookmarks_tab, searches_tab, comparisons_tab = st.tabs(
        ["Bookmarks", "Search history", "Saved comparisons"]
    )

    with bookmarks_tab:
        if not bookmarks:
            st.info("No bookmarked vehicles yet. Add one from Vehicles.")
        for bookmark in bookmarks:
            with st.container(border=True):
                st.subheader(bookmark["vehicle_name"])
                data = bookmark["vehicle_data"]
                summary_fields = [
                    ("Model year", data.get("model_year")),
                    ("Fuel", data.get("fuel_display", data.get("fuel_type"))),
                    ("Power", data.get("power_hp")),
                    ("Body type", data.get("body_type")),
                ]
                summary = " · ".join(
                    f"{label}: {value}"
                    for label, value in summary_fields
                    if value not in (None, "", "Unknown")
                )
                if summary:
                    st.write(summary)

                with st.form(
                    key=f"bookmark_form_{profile_id}_{bookmark['vehicle_key']}"
                ):
                    note = st.text_area(
                        "Notes",
                        value=bookmark["note"],
                        placeholder="Why are you considering this vehicle?",
                        key=f"bookmark_note_{profile_id}_{bookmark['vehicle_key']}",
                    )
                    save_col, delete_col = st.columns(2)
                    save_note = save_col.form_submit_button(
                        "Save note",
                        key=f"save_bookmark_note_{profile_id}_{bookmark['vehicle_key']}",
                    )
                    remove_bookmark = delete_col.form_submit_button(
                        "Delete bookmark",
                        key=f"delete_bookmark_{profile_id}_{bookmark['vehicle_key']}",
                    )

                if save_note:
                    updated = user_features.update_bookmark_note(
                        profile_id, bookmark["vehicle_key"], note
                    )
                    if updated:
                        st.session_state[feedback_key] = (
                            "success",
                            "Bookmark note saved.",
                        )
                    else:
                        st.session_state[feedback_key] = (
                            "warning",
                            "Bookmark no longer exists; it may have been removed.",
                        )
                    st.rerun()
                if remove_bookmark:
                    deleted = user_features.delete_bookmark(
                        profile_id, bookmark["vehicle_key"]
                    )
                    if deleted:
                        st.session_state[feedback_key] = (
                            "success",
                            "Bookmark deleted.",
                        )
                    else:
                        st.session_state[feedback_key] = (
                            "warning",
                            "Bookmark no longer exists; it may already have been removed.",
                        )
                    st.rerun()

    with searches_tab:
        if not searches:
            st.info("Search for a vehicle to start your history.")
        else:
            if st.button("Clear search history", key="clear_dashboard_searches"):
                user_features.clear_search_history(profile_id)
                st.rerun()
            for search in searches:
                query_col, date_col, delete_col = st.columns([4, 3, 1])
                query_col.write(search["query"])
                date_col.caption(search["searched_at"])
                if delete_col.button(
                    "Delete", key=f"remove_search_{search['id']}"
                ):
                    user_features.delete_search(profile_id, search["id"])
                    st.rerun()

    with comparisons_tab:
        if not comparisons:
            st.info("No saved comparisons yet. Save one from Compare.")
        for comparison in comparisons:
            with st.container(border=True):
                title_col, date_col, delete_col = st.columns([5, 3, 1])
                title_col.subheader(" vs ".join(comparison["vehicle_names"]))
                date_col.caption(comparison["saved_at"])
                if delete_col.button(
                    "Delete", key=f"remove_comparison_{comparison['id']}"
                ):
                    user_features.delete_comparison(profile_id, comparison["id"])
                    st.rerun()

                fields = [
                    ("Model year", "model_year"),
                    ("Body type", "body_type"),
                    ("Fuel type", "fuel_display"),
                    ("Power (hp)", "power_hp"),
                    ("Transmission", "transmission"),
                    ("Drivetrain", "drivetrain"),
                ]
                rows = []
                for label, field in fields:
                    row = {"Specification": label}
                    for vehicle in comparison["vehicle_data"]:
                        value = vehicle.get(field)
                        row[vehicle["Vehicle"]] = (
                            "Not available" if value is None else str(value)
                        )
                    rows.append(row)
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
