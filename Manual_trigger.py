import pandas as pd
from datetime import datetime, timedelta
from email.message import EmailMessage
import smtplib
from config import db_run_query  # your DB helper

# Detect if running in Streamlit
try:
    import streamlit as st
    USING_STREAMLIT = True
except ImportError:
    USING_STREAMLIT = False
    from dotenv import load_dotenv
    load_dotenv()
    import os

def send_expiry_email():
    # --- Load credentials ---
    if USING_STREAMLIT:
        EMAIL_ADDRESS = st.secrets.get("EMAIL_ADDRESS")
        EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD")
        recipients_secret = st.secrets.get("RECIPIENTS", "")
    else:
        import os
        EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
        EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
        recipients_secret = os.environ.get("RECIPIENTS", "")

    # --- Convert recipients to list safely ---
    if isinstance(recipients_secret, str):
        # Split by comma and strip quotes/spaces
        RECIPIENTS = [r.strip().strip('\'"') for r in recipients_secret.split(",") if r.strip()]
    elif isinstance(recipients_secret, list):
        # Strip quotes/spaces from each item
        RECIPIENTS = [r.strip().strip('\'"') for r in recipients_secret if r.strip()]
    else:
        RECIPIENTS = []

    if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, RECIPIENTS]):
        msg = "❌ Email credentials or recipients are missing!"
        if USING_STREAMLIT:
            st.error(msg)
        else:
            print(msg)
        return

    # --- Fetch products from DB ---
    try:
        df = db_run_query("SELECT product_name, expiry_date FROM products;")
    except Exception as e:
        msg = f"❌ Failed to fetch products: {e}"
        if USING_STREAMLIT:
            st.error(msg)
        else:
            print(msg)
        return

    if df.empty or "expiry_date" not in df.columns:
        msg = "ℹ️ No products found in database."
        if USING_STREAMLIT:
            st.info(msg)
        else:
            print(msg)
        return

    # --- Convert expiry_date to datetime.date safely ---
    df["expiry_date"] = pd.to_datetime(df["expiry_date"], errors="coerce").dt.date

    # --- Filter products expiring within 3 days ---
    threshold = datetime.today().date() + timedelta(days=3)
    expiring_soon = [r for r in df.itertuples(index=False) if r.expiry_date and r.expiry_date <= threshold]

    if not expiring_soon:
        msg = "ℹ️ No products expiring within 3 days."
        if USING_STREAMLIT:
            st.info(msg)
        else:
            print(msg)
        return

    # --- Prepare and send email ---
    msg_email = EmailMessage()
    msg_email['Subject'] = "Products Expiring Soon!"
    msg_email['From'] = EMAIL_ADDRESS
    msg_email['To'] = ", ".join(RECIPIENTS)
    msg_email.set_content("\n".join([f"{r.product_name} expires on {r.expiry_date}" for r in expiring_soon]))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg_email)
        msg = f"✅ Expiry email sent successfully to {len(RECIPIENTS)} recipient(s)!"
        if USING_STREAMLIT:
            st.success(msg)
        else:
            print(msg)
    except Exception as e:
        msg = f"❌ Error sending email: {e}"
        if USING_STREAMLIT:
            st.error(msg)
        else:
            print(msg)
