import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
from login_supabase import supabase

# -------------------------
# Login Page
# -------------------------
def login_page():
    st.title("🔑 ZeroDump Login")

    auth_method = st.radio("Choose login method:", ["Email & Password", "Google"])

    if auth_method == "Email & Password":
        option = st.radio("Do you want to:", ["Login", "Register"])
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if option == "Register":
            if st.button("Sign Up"):
                try:
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.success("✅ Account created! Please verify your email.")
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
                st.write("👉 Open this link to log in with Google:")
                st.write(res.url)
            except Exception as e:
                st.error(f"❌ {e}")