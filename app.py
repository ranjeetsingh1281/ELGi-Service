import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ==============================
# 🔐 HARD-CODED CONFIG (Testing Only)
# ==============================
# 💡 APNE SUPABASE SE COPY KARKE YAHAN PASTE KAREIN:
URL = "https://your-project-id.supabase.co" # <--- Yahan URL daalein
KEY = "your-anon-key-here"                  # <--- Yahan Key daalein

try:
    # URL aur Key ko clean karke client banana
    supabase: Client = create_client(URL.strip(), KEY.strip())
    st.sidebar.success("✅ Supabase Client Ready!")
except Exception as e:
    st.sidebar.error(f"❌ Initialization Failed: {e}")

# ==============================
# 🔍 TEST CONNECTION BUTTON
# ==============================
st.sidebar.title("🛠️ Debug Tools")
if st.sidebar.button("🔍 Test DB Connection"):
    try:
        # Ek chota sa test call 'machines' table par
        res = supabase.table("machines").select("count", count="exact").limit(1).execute()
        st.sidebar.write(f"📊 Connection Live! Rows: {res.count}")
    except Exception as e:
        st.sidebar.error(f"❌ Cannot talk to DB: {e}")
        st.sidebar.info("💡 Tip: Check if your IP is allowed in Supabase or URL is wrong.")

# ==============================
# ⚡ SYNC ENGINE (Small Batch Test)
# ==============================
st.title("⚡ ELGi Cloud Sync - Final Test")
st.write("Is code mein URL seedha code ke andar hai. Check kijiye ki kya connection banta hai.")

s_file = st.file_uploader("Upload Service_Details.xlsx", type="xlsx")

if s_file and st.button("🚀 Start Small Sync (First 100)"):
    try:
        with st.spinner("Processing Excel..."):
            df = pd.read_excel(s_file).fillna("N/A")
            
        srv_list = []
        # Sirf pehle 100 records test ke liye
        for _, row in df.head(100).iterrows():
            srv_list.append({
                "fabrication_id": str(row.get('Fabrication Number', row.get('Fabrication', ''))).strip(),
                "service_date": str(pd.to_datetime(row.get('Visit Date', '2024-01-01')).date()),
                "description": f"Test: {str(row.get('Service Done', 'N/A'))}",
                "technician_name": str(row.get('Engineer', 'Admin'))
            })
        
        if srv_list:
            # Batch upload test
            supabase.table("service_logs").upsert(srv_list).execute()
            st.success("✅ First 100 records synced successfully to Cloud!")
            st.balloons()
        else:
            st.warning("Excel format mismatch.")
            
    except Exception as e:
        st.error(f"❌ Sync failed: {e}")
        st.info("Check if 'service_logs' table exists in Supabase SQL Editor.")

# Sidebar Status Metric
if st.sidebar.button("📈 Check Total Records"):
    res = supabase.table("service_logs").select("id", count="exact").execute()
    st.sidebar.metric("Total in Cloud", res.count)
