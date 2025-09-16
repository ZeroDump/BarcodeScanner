import streamlit as st
from streamlit.runtime.scriptrunner import RerunException
from utils.login_func import login_page
from livescan import livescan

# --- Main Router ---
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if st.session_state["logged_in"]:
        livescan()
        if st.button("🚪 Logout"):
            st.session_state["logged_in"] = False
            st.session_state.pop("user", None)
    else:
        login_page()


if __name__ == "__main__":
    main()
