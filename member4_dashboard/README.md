# Member 4 Dashboard

Integrated into the main VehicleWise Streamlit app. It uses the shared `vehicle_data.py` catalogue and stores bookmarks, notes, search history, and saved comparisons in `user_features.sqlite3` inside this folder.

Install the UI dependencies from the project directory:

```powershell
python -m pip install -r member4_dashboard/requirements.txt
```

Run the complete app, including Explore, Compare, Catalogue, Recommendations, and My dashboard:

```powershell
python -m streamlit run app.py
```

The standalone Member 4 UI is also available with `python -m streamlit run member4_dashboard/app.py`.

The profile ID is a local demo identifier, not authentication. The app uses `st.session_state.user_id` when an authenticated login flow provides it.
