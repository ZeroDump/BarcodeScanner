import streamlit as st
from supabase import create_client
from login_supabase import supabase

def login_page():
    st.title("🔑 ZeroDump Login")

    # -------------------------
    # Fetch store list
    # -------------------------
    try:
        stores_response = supabase.table("stores").select("store_id, store_name").execute()

        if stores_response.data:
            store_names = [store["store_name"] for store in stores_response.data]
        else:
            store_names = []

    except Exception as e:
        if "JWT expired" in str(e):
            st.warning("⚠️ Your session has expired. Please log in again.")
            st.session_state.clear()  # reset session so user can re-login
        else:
            st.error(f"❌ Could not fetch store list: {e}")
        store_names = []

    # -------------------------
    # Auth Section
    # -------------------------
    auth_method = st.radio("Choose login method:", ["Email & Password", "Google"])

    if auth_method == "Email & Password":
        option = st.radio("Do you want to:", ["Login", "Register"])
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if option == "Register":
            name = st.text_input("Name")
            store_name = st.selectbox("Select Store", store_names if store_names else ["No stores found"])

            if st.button("Sign Up"):
                try:
                    # Create the user
                    auth_res = supabase.auth.sign_up({"email": email, "password": password})
                    if auth_res.user:
                        # Find selected store_id
                        selected_store = next((s for s in stores_response.data if s["store_name"] == store_name), None)
                        store_id = selected_store["store_id"] if selected_store else None

                        # Insert into user_profiles using the correct user_id
                        supabase.table("user_profiles").insert({
                            "user_id": auth_res.user.id,
                            "name": name,
                            "store_id": store_id
                        }).execute()

                        st.success("✅ Account created! Please verify your email.")
                    else:
                        st.error("❌ Could not create account.")
                except Exception as e:
                    st.error(f"❌ {e}")
        elif option == "Login":
            if st.button("Login"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state["user"] = res.user
                        st.session_state["logged_in"] = True
                        st.success("✅ Logged in successfully!")
                    else:
                        st.error("❌ Invalid login.")
                except Exception as e:
                    st.error(f"❌ {e}")

    elif auth_method == "Google":
        if st.button("Login with Google"):
            try:
                res = supabase.auth.sign_in_with_oauth({"provider": "google"})
                st.info("👉 Open this link to log in with Google:")
                st.write(res.url)
            except Exception as e:
                st.error(f"❌ {e}")
