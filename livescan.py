import streamlit as st
import cv2
import numpy as np
import requests
from datetime import datetime, date
from config import db_run_query  # 👈 your DB helper
from Manual_trigger import send_expiry_email  # 👈 reuse email function

st.title("📷 Grocery Barcode Scanner (Cloud-Friendly with DB)")

# ----------------- Camera Input -----------------
img_file = st.camera_input("Take a picture of the barcode")

if img_file:
    if "barcode_data" not in st.session_state:
        # Convert image to OpenCV format
        file_bytes = np.asarray(bytearray(img_file.getvalue()), dtype=np.uint8)
        frame = cv2.imdecode(file_bytes, 1)
        is_success, buffer = cv2.imencode(".jpg", frame)

        if is_success:
            files = {"f": ("barcode.jpg", buffer.tobytes(), "image/jpeg")}
            api_url = "https://zxing.org/w/decode"
            response = requests.post(api_url, files=files)

            if response.status_code == 200 and "Parsed Result" in response.text:
                start = response.text.find("<pre>") + 5
                end = response.text.find("</pre>")
                st.session_state.barcode_data = response.text[start:end].strip()
            else:
                st.error("Error contacting ZXing API or barcode could not be detected.")

    # If barcode detected
    if "barcode_data" in st.session_state:
        barcode_data = st.session_state.barcode_data
        st.success(f"✅ Detected barcode: {barcode_data}")

        # --- OpenFoodFacts API ---
        if "product_name" not in st.session_state:
            url = f"https://world.openfoodfacts.org/api/v0/product/{barcode_data}.json"
            try:
                res = requests.get(url, timeout=5).json()
            except Exception:
                res = {}
            if res.get("status") == 1:
                product = res.get("product", {})
                st.session_state.product_name = product.get("product_name", "Unknown Product")
                st.session_state.brand = product.get("brands", "Unknown")
                st.session_state.quantity = product.get("quantity", "Unknown")
            else:
                st.session_state.product_name = "Unknown Product"
                st.session_state.brand = "Unknown"
                st.session_state.quantity = "Unknown"

        st.subheader(st.session_state.product_name)
        st.write(f"**Brand:** {st.session_state.brand}")
        st.write(f"**Quantity:** {st.session_state.quantity}")

        # --- Expiry Date Input ---
        expiry_date = st.date_input("📅 Enter expiry date", min_value=date.today())

        # --- Save to DB ---
        if st.button("💾 Save to Database"):
            insert_query = """
                INSERT INTO products (barcode, product_name, expiry_date, created_at)
                VALUES (%s, %s, %s, %s);
            """
            db_run_query(insert_query, params=(
                barcode_data,
                st.session_state.product_name,
                str(expiry_date),
                datetime.now()
            ))
            st.success("✅ Product saved to database!")

# ----------------- Show Database -----------------
if st.checkbox("📑 Show saved records"):
    df = db_run_query("SELECT * FROM products ORDER BY created_at DESC;")
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("No products saved yet.")

# --- Streamlit button ---
if st.button("📧 Send Expiry Email Now"):
    send_expiry_email()
    st.success("✅ Expiry email triggered!")