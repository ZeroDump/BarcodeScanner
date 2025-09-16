from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
from config import db_run_query
import os
import pandas as pd
from dotenv import load_dotenv
import io
from zoneinfo import ZoneInfo  # built-in since Python 3.9

# Load env variables
load_dotenv()
EMAIL_ADDRESS = os.environ['EMAIL_ADDRESS']
EMAIL_PASSWORD = os.environ['EMAIL_PASSWORD']
RECIPIENTS = os.environ['RECIPIENTS'].split(',')  # comma-separated list

# Query the database ---
df = db_run_query("SELECT product_name, expiry_date FROM products;")

# Process data
# Get "today" in EST (handles EDT in summer automatically)
today = datetime.now(ZoneInfo("America/New_York")).date()
today = datetime.today().date()
tomorrow = today + timedelta(days=1)
threshold = today + timedelta(days=3)

# Ensure expiry_date is a date
df["expiry_date"] = pd.to_datetime(df["expiry_date"]).dt.date

# Filter between tomorrow and threshold
expiring_soon = df[(df["expiry_date"] >= tomorrow) & (df["expiry_date"] <= threshold)]

# --- Create CSV directly in memory ---
csv_buffer = io.StringIO()
expiring_soon.to_csv(csv_buffer, index=False)
csv_bytes = csv_buffer.getvalue().encode("utf-8")

# Send email if needed ---
if not expiring_soon.empty:
    tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    msg = EmailMessage()
    msg["Subject"] = f"📦 Products Expiring soon! {tomorrow}"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ", ".join(RECIPIENTS)

    body = "Hi,\n\nPlease find attached the list of products expiring in the next 3 days:\n\n"
    body += "\n".join([f"- {row.product_name} expires on {row.expiry_date}"
                    for row in expiring_soon.itertuples()])
    body += "\n\nPlease take necessary action."
    body += "\n\nRegards,\nExpiry Tracker"
    msg.set_content(body)

    # --- Attach to email ---
    msg.add_attachment(
        csv_bytes,
        maintype="text",
        subtype="csv",
        filename="expiring_products.csv"
)
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        print("✅ Email sent successfully!")
    except Exception as e:
        print("❌ Error sending email:", e)
else:
    print("No products expiring soon.")