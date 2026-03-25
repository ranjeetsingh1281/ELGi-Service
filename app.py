import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# ==============================
# 🔐 SUPABASE CONFIG (Cleaned)
# ==============================
if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
    URL = st.secrets["SUPABASE_URL"].strip().rstrip('/')
    KEY = st.secrets["SUPABASE_KEY"].strip()
    supabase: Client = create_client(URL, KEY)
else:
    st.error("🚨 Secrets missing!")
    st.stop()

# ==============================
# 📤 MIGRATION LOGIC (Robust)
# ==============================
def clean_val(val, default=0.0):
    try:
        if pd.isna(val) or val == "": return default
        return float(val)
    except: return default

def upload_to_supabase(df, tracker_type):
    st.info(f"🚀 Uploading {len(df)} records for {tracker_type}...")
    pb = st.progress(0)
    
    for i, row in df.iterrows():
        try:
            # Fabrication ID extraction
            fab_id = str(row.get('Fabrication Number', row.get('Fabrication', ''))).strip()
            if not fab_id or fab_id == "0" or fab_id == "0.0": continue

            data = {
                "fabrication_id": fab_id,
                "customer_name": str(row.get('Customer', 'Unknown')),
                "category": str(row.get('Category', 'N/A')),
                "unit_status": str(row.get('Unit Status', 'Active')),
                "avg_running_hrs": clean_val(row.get('Average Running Hours', row.get('Avg. Running', 0))),
                "current_hmr": clean_val(row.get('Current Hours', row.get('CURRENT HMR', 0))),
                "total_hours_dn": clean_val(row.get('Total Hours', row.get('MDA Total Hours', 0))),
                "last_service_date": str(pd.to_datetime(row.get('Last Call Date', '2024-01-01')).date()),
                "tracker_type": tracker_type
            }
            
            # Cloud Upsert
            supabase.table("machines").upsert(data).execute()
            
            if i % 10 == 0:
                pb.progress((i + 1) / len(df))
                time.sleep(0.05) # Prevention of network congestion
                
        except Exception as e:
            st.error(f"Row {i} (ID: {fab_id}) failed: {e}")
            
    st.success(f"✅ Migration for {tracker_type} Completed!")

# --- UI ---
st.title("📤 Migration Center - Prime Power")
t_type = st.selectbox("Select Tracker Type", ["DPSAC", "INDUSTRIAL"])
uploaded_file = st.file_uploader("Upload Excel File", type="xlsx")

if uploaded_file and st.button("Start Cloud Sync"):
    df_excel = pd.read_excel(uploaded_file, engine='openpyxl')
    upload_to_supabase(df_excel, t_type)
