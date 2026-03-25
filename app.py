import streamlit as st
import pandas as pd
from supabase import create_client, Client

# ==============================
# 🔐 SUPABASE CONFIG
# ==============================
URL = st.secrets["SUPABASE_URL"].strip().rstrip('/')
KEY = st.secrets["SUPABASE_KEY"].strip()
supabase: Client = create_client(URL, KEY)

# ==============================
# 📤 MIGRATION LOGIC (For FOC & Service Details)
# ==============================
def upload_foc(df):
    st.info(f"📦 Uploading {len(df)} FOC Records...")
    for _, row in df.iterrows():
        data = {
            "fabrication_id": str(row.get('Fabrication Number', row.get('Fabrication', ''))).strip(),
            "description": str(row.get('Description', row.get('Item', 'N/A'))),
            "service_date": str(pd.to_datetime(row.get('Date', '2024-01-01')).date())
        }
        supabase.table("service_logs").upsert(data).execute() # Using service_logs table for simplicity
    st.success("✅ FOC Sync Success!")

def upload_service_details(df):
    st.info(f"🕒 Uploading {len(df)} Service Visits...")
    for _, row in df.iterrows():
        data = {
            "fabrication_id": str(row.get('Fabrication Number', row.get('Fabrication', ''))).strip(),
            "service_date": str(pd.to_datetime(row.get('Visit Date', '2024-01-01')).date()),
            "description": str(row.get('Service Done', 'N/A')),
            "technician_name": str(row.get('Engineer', 'Admin'))
        }
        supabase.table("service_logs").upsert(data).execute()
    st.success("✅ Service Details Sync Success!")

# ==============================
# 🏢 UI - MIGRATION CENTER
# ==============================
st.title("📤 Multi-File Cloud Sync")

# Tabs for different syncs
t1, t2, t3 = st.tabs(["1. Master Sync", "2. FOC Sync", "3. Service History Sync"])

with t1:
    st.subheader("Master Data Sync")
    # (Purana Master Sync wala code yahan rahega)
    st.info("Aapne Industrial Master pehle hi kar liya hai. DPSAC Master baki hai.")

with t2:
    st.subheader("📦 Sync Active FOC")
    foc_file = st.file_uploader("Upload Active_FOC.xlsx", type="xlsx")
    if foc_file and st.button("Sync FOC to Cloud"):
        df_foc = pd.read_excel(foc_file, engine='openpyxl')
        upload_foc(df_foc)

with t3:
    st.subheader("🕒 Sync Service Details")
    srv_file = st.file_uploader("Upload Service_Details.xlsx", type="xlsx")
    if srv_file and st.button("Sync History to Cloud"):
        df_srv = pd.read_excel(srv_file, engine='openpyxl')
        upload_service_details(df_srv)
