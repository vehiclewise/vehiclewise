import os
import requests
import streamlit as st
from datetime import date

API_URL = os.getenv("VEHICLEWISE_API_URL", "http://127.0.0.1:8000").rstrip("/")


def _show_api_error(response, fallback):
    """Display a useful API error without assuming every response is JSON."""
    try:
        detail = response.json().get("detail", fallback)
    except (ValueError, AttributeError):
        detail = fallback
    st.error(detail)


def _parse_optional_date(value):
    """Return an ISO date string, or None when the field is blank."""
    value = value.strip()
    if not value:
        return None

    parsed = date.fromisoformat(value)
    if parsed > date.today():
        raise ValueError("Date of birth cannot be in the future.")
    return parsed.isoformat()


def require_authentication():
    # --------------------------------------------------
    # SESSION STATE
    # --------------------------------------------------
    if "access_token" not in st.session_state:
        st.session_state.access_token = None

    if "user" not in st.session_state:
        st.session_state.user = None

    # --------------------------------------------------
    # RESET PASSWORD PAGE
    # --------------------------------------------------
    reset_token = st.query_params.get("reset_token")

    if reset_token:
        st.title("🚗 VehicleWise")
        st.subheader("Reset your password")
        st.write("Choose a new password for your account.")

        with st.form("reset_password_form"):
            new_password = st.text_input("New password", type="password")
            confirm_password = st.text_input(
                "Confirm new password", type="password"
            )
            reset_button = st.form_submit_button(
                "Reset Password", use_container_width=True
            )

        if reset_button:
            if len(new_password) < 8:
                st.error("Password must contain at least 8 characters.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                try:
                    response = requests.post(
                        f"{API_URL}/auth/reset-password",
                        json={
                            "token": reset_token,
                            "new_password": new_password,
                        },
                        timeout=15,
                    )
                    if response.status_code == 200:
                        st.success(
                            "Password reset successful! You can now log in."
                        )
                        st.query_params.clear()
                        st.rerun()
                    else:
                        _show_api_error(response, "Password reset failed.")
                except requests.RequestException:
                    st.error(
                        "Cannot connect to the authentication server."
                    )

        st.stop()

    # --------------------------------------------------
    # VERIFY EXISTING LOGIN
    # --------------------------------------------------
    if st.session_state.access_token:
        headers = {
            "Authorization": f"Bearer {st.session_state.access_token}"
        }
        try:
            response = requests.get(
                f"{API_URL}/auth/me", headers=headers, timeout=5
            )
            if response.status_code == 200:
                st.session_state.user = response.json()
            else:
                st.session_state.access_token = None
                st.session_state.user = None
        except requests.RequestException:
            st.error("Cannot connect to the authentication server.")
            st.stop()

    # --------------------------------------------------
    # LOGIN AND REGISTRATION
    # --------------------------------------------------
    if not st.session_state.access_token:
        st.title("🚗 VehicleWise")
        st.subheader("Welcome to VehicleWise")
        st.write("Sign in or create an account to continue.")

        login_tab, register_tab = st.tabs(["Login", "Register"])

        # LOGIN
        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Email address")
                password = st.text_input("Password", type="password")
                login_button = st.form_submit_button(
                    "Login", use_container_width=True
                )

            if login_button:
                try:
                    response = requests.post(
                        f"{API_URL}/auth/login",
                        json={
                            "email": email.strip(),
                            "password": password,
                        },
                        timeout=10,
                    )
                    if response.status_code == 200:
                        st.session_state.access_token = response.json()[
                            "access_token"
                        ]
                        st.session_state.user = None
                        st.rerun()
                    else:
                        _show_api_error(response, "Login failed.")
                except requests.RequestException:
                    st.error(
                        "Cannot connect to the authentication server."
                    )

            # FORGOT PASSWORD
            with st.expander("Forgot your password?"):
                st.write(
                    "Enter your registered email address to request "
                    "a password-reset link."
                )
                with st.form("forgot_password_form"):
                    forgot_email = st.text_input(
                        "Registered email address"
                    )
                    forgot_button = st.form_submit_button(
                        "Send Reset Link", use_container_width=True
                    )

                if forgot_button:
                    try:
                        response = requests.post(
                            f"{API_URL}/auth/forgot-password",
                            json={"email": forgot_email.strip()},
                            timeout=20,
                        )
                        if response.status_code == 200:
                            try:
                                st.success(response.json()["message"])
                            except (ValueError, KeyError):
                                st.success(
                                    "If the account exists, a reset "
                                    "message will be sent."
                                )
                        else:
                            _show_api_error(
                                response, "Unable to process request."
                            )
                    except requests.RequestException:
                        st.error(
                            "Cannot connect to the authentication server."
                        )

        # REGISTRATION — PERSONAL AND ACCOUNT DETAILS ONLY
        with register_tab:
            with st.form("register_form"):
                st.markdown("### Account details")
                username = st.text_input("Username")
                reg_email = st.text_input("Email address")
                reg_password = st.text_input(
                    "Password", type="password"
                )
                confirm_password = st.text_input(
                    "Confirm password", type="password"
                )

                st.divider()
                st.markdown("### Personal information")
                full_name = st.text_input("Full name")
                date_of_birth = st.text_input(
                    "Date of birth (YYYY-MM-DD, optional)",
                    placeholder="e.g. 2000-05-15",
                )
                phone_number = st.text_input("Phone number (optional)")
                country = st.text_input("Country")
                city = st.text_input("City (optional)")

                register_button = st.form_submit_button(
                    "Create account", use_container_width=True
                )

            if register_button:
                if not username.strip() or not reg_email.strip():
                    st.error("Username and email are required.")
                elif len(username.strip()) < 3:
                    st.error("Username must contain at least 3 characters.")
                elif not full_name.strip() or not country.strip():
                    st.error("Full name and country are required.")
                elif len(reg_password) < 8:
                    st.error("Password must contain at least 8 characters.")
                elif reg_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    try:
                        parsed_dob = _parse_optional_date(date_of_birth)
                    except ValueError as error:
                        st.error(
                            str(error)
                            if str(error)
                            else "Enter a valid date in YYYY-MM-DD format."
                        )
                    else:
                        registration_data = {
                            "username": username.strip(),
                            "email": reg_email.strip(),
                            "password": reg_password,
                            "full_name": full_name.strip(),
                            "date_of_birth": parsed_dob,
                            "phone_number": phone_number.strip() or None,
                            "country": country.strip(),
                            "city": city.strip() or None,
                        }
                        try:
                            response = requests.post(
                                f"{API_URL}/auth/register",
                                json=registration_data,
                                timeout=10,
                            )
                            if response.status_code == 201:
                                st.success(
                                    "Account created successfully! "
                                    "Please log in."
                                )
                            else:
                                _show_api_error(
                                    response, "Registration failed."
                                )
                        except requests.RequestException:
                            st.error(
                                "Cannot connect to the authentication server."
                            )

        st.stop()

    # --------------------------------------------------
    # LOGGED-IN USER
    # --------------------------------------------------
    user = st.session_state.user or {}
    st.sidebar.divider()
    st.sidebar.subheader("👤 My Account")
    st.sidebar.success(f"Logged in as {user.get('username', 'User')}")

    # --------------------------------------------------
    # MY PROFILE — PERSONAL INFORMATION ONLY
    # --------------------------------------------------
    with st.sidebar.expander("My Profile"):
        st.write("**Account Details**")
        st.write(f"User ID: {user.get('id', '')}")
        st.write(f"Username: {user.get('username', '')}")
        st.write(f"Email: {user.get('email', '')}")

        st.divider()
        st.write("**Personal Information**")

        with st.form("update_profile_form"):
            updated_username = st.text_input(
                "Username", value=user.get("username") or ""
            )
            updated_email = st.text_input(
                "Email address", value=user.get("email") or ""
            )
            updated_full_name = st.text_input(
                "Full name", value=user.get("full_name") or ""
            )
            updated_dob = st.text_input(
                "Date of birth (YYYY-MM-DD)",
                value=user.get("date_of_birth") or "",
            )
            updated_phone = st.text_input(
                "Phone number", value=user.get("phone_number") or ""
            )
            updated_country = st.text_input(
                "Country", value=user.get("country") or ""
            )
            updated_city = st.text_input(
                "City", value=user.get("city") or ""
            )

            update_button = st.form_submit_button(
                "Save Profile Changes", use_container_width=True
            )

        if update_button:
            if len(updated_username.strip()) < 3:
                st.error("Username must contain at least 3 characters.")
            elif not updated_email.strip():
                st.error("Email address is required.")
            elif not updated_full_name.strip():
                st.error("Full name is required.")
            elif not updated_country.strip():
                st.error("Country is required.")
            else:
                try:
                    parsed_profile_dob = _parse_optional_date(updated_dob)
                except ValueError as error:
                    st.error(
                        str(error)
                        if str(error)
                        else "Enter date of birth as YYYY-MM-DD."
                    )
                else:
                    headers = {
                        "Authorization": (
                            f"Bearer {st.session_state.access_token}"
                        )
                    }
                    # Vehicle preferences are intentionally not included.
                    # The profile API therefore leaves them unchanged.
                    profile_data = {
                        "username": updated_username.strip(),
                        "email": updated_email.strip(),
                        "full_name": updated_full_name.strip(),
                        "date_of_birth": parsed_profile_dob,
                        "phone_number": updated_phone.strip() or None,
                        "country": updated_country.strip(),
                        "city": updated_city.strip() or None,
                    }

                    try:
                        response = requests.put(
                            f"{API_URL}/auth/me",
                            headers=headers,
                            json=profile_data,
                            timeout=10,
                        )
                        if response.status_code == 200:
                            st.session_state.user = response.json()
                            st.success("Profile updated successfully!")
                            st.rerun()
                        else:
                            _show_api_error(
                                response, "Profile update failed."
                            )
                    except requests.RequestException:
                        st.error(
                            "Cannot connect to the authentication server."
                        )

    # --------------------------------------------------
    # CHANGE PASSWORD
    # --------------------------------------------------
    with st.sidebar.expander("Change Password"):
        with st.form("change_password_form"):
            current_password = st.text_input(
                "Current password", type="password"
            )
            new_password = st.text_input(
                "New password", type="password"
            )
            confirm_new_password = st.text_input(
                "Confirm new password", type="password"
            )
            change_button = st.form_submit_button(
                "Update Password", use_container_width=True
            )

        if change_button:
            if len(new_password) < 8:
                st.error(
                    "New password must contain at least 8 characters."
                )
            elif new_password != confirm_new_password:
                st.error("New passwords do not match.")
            else:
                headers = {
                    "Authorization": (
                        f"Bearer {st.session_state.access_token}"
                    )
                }
                try:
                    response = requests.post(
                        f"{API_URL}/auth/change-password",
                        headers=headers,
                        json={
                            "current_password": current_password,
                            "new_password": new_password,
                        },
                        timeout=10,
                    )
                    if response.status_code == 200:
                        st.sidebar.success(
                            "Password changed successfully!"
                        )
                    else:
                        _show_api_error(
                            response, "Password change failed."
                        )
                except requests.RequestException:
                    st.sidebar.error(
                        "Cannot connect to the authentication server."
                    )

    # --------------------------------------------------
    # LOGOUT
    # --------------------------------------------------
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.access_token = None
        st.session_state.user = None
        st.rerun()

    return user
