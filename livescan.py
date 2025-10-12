def livescan():
    import streamlit as st
    import cv2
    import numpy as np
    import requests
    from datetime import datetime, date
    from config import db_run_query
    from Manual_trigger import send_expiry_email
    from login_supabase import supabase

    # ----------------- Display User & Store -----------------
    if "user" in st.session_state:
        user_id = st.session_state.user.id  # UID from Supabase

        # Fetch user profile
        profile_res = supabase.table("user_profiles").select("name, store_id").eq("user_id", user_id).execute()
        if profile_res.data:
            profile = profile_res.data[0]
            name = profile.get("name", "Unknown User")
            store_id = profile.get("store_id", None)

            # Fetch store name
            store_res = supabase.table("stores").select("store_name").eq("store_id", store_id).execute()
            store_name = store_res.data[0]["store_name"] if store_res.data else "Unknown Store"

            st.title(f"🏬 Store: {store_name}")
            st.subheader(f"Welcome, {name}!")
        else:
            st.warning("⚠️ User profile not found.")
    else:
        st.warning("⚠️ Please log in first.")
        return  # Stop here if user not logged in

    # ----------------- Camera Input -----------------
    img_file = st.camera_input("Take a picture of the barcode")

    # Reset cache only when the photo changes (new or cleared)
    if img_file != st.session_state.get("last_photo", None):
        for key in ["barcode_data", "product_name", "brand", "quantity"]:
            st.session_state.pop(key, None)
        st.session_state.last_photo = img_file

    # ----------------- Barcode Processing -----------------
    if img_file:
        if "barcode_data" not in st.session_state:
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

            expiry_date = st.date_input("📅 Enter expiry date", min_value=date.today())
            product_count = st.number_input("📦 Enter product count", min_value=1, step=1)

            if st.button("💾 Save to Database"):
                # --- Fetch user and store info ---
                user_id = st.session_state.user.id

                # Get user details (name, store_id)
                profile_res = supabase.table("user_profiles").select("name, store_id").eq("user_id", user_id).execute()
                if not profile_res.data:
                    st.error("User profile not found — cannot save product.")
                    return

                profile = profile_res.data[0]
                user_name = profile.get("name")
                store_id = profile.get("store_id")

                # Get store name
                store_res = supabase.table("stores").select("store_name").eq("store_id", store_id).execute()
                store_name = store_res.data[0]["store_name"] if store_res.data else "Unknown Store"
                insert_query = """
                    INSERT INTO products (barcode, product_name, brand, quantity, product_count, expiry_date, created_at, user_id, user_name, store_id, store_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
                db_run_query(insert_query, params=(
                    barcode_data,
                    st.session_state.product_name,
                    st.session_state.brand,
                    st.session_state.quantity,
                    product_count,
                    expiry_date,
                    datetime.now(),
                    user_id,
                    user_name,
                    store_id,
                    store_name
                ))
                st.success(f"✅ Product saved for {store_name} by {user_name}!")

                # Reset state
                for key in ["barcode_data", "product_name", "brand", "quantity"]:
                    st.session_state.pop(key, None)

                st.rerun()

    # ----------------- Show Database -----------------
    if st.checkbox("📑 Show saved records"):
        df = db_run_query("SELECT product_name, brand, quantity, product_count, expiry_date, store_name, user_name, user_id FROM products ORDER BY created_at DESC;")
        if not df.empty:
            st.dataframe(df)
        else:
            st.info("No products saved yet.")


    if st.button("📧 Send Expiry Email Now"):
        send_expiry_email()
        st.success("✅ Expiry email triggered!")

    if st.button("Logout"):
        st.session_state.clear()
        st.session_state["page"] = "login"
