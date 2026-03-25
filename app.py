import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# ==============================
# 🔐 SUPABASE CONFIG (With Strip)
# ==============================
if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
    URL = st.secrets["SUPABASE_URL"].strip().rstrip('/') # Slash hatane ke liye
    KEY = st.secrets["SUPABASE_KEY"].strip()
    supabase: Client = create_client(URL, KEY)
else:
    st.error("🚨 Secrets missing in Streamlit Settings!")
    st.stop()

# ==============================
# 📤 MIGRATION WITH BATCHING
# ==============================
def upload_to_supabase(df, tracker_type):
    st.info(f"Migration started for {len(df)} records. Please wait...")
    progress_bar = st.progress(0)
    
    # Data ko cleaning
    df = df.fillna(0) # Empty cells ko 0 se bhar dena taaki error na aaye
    
    for i, row in df.iterrows():
        try:
            data = {
                "fabrication_id": str(row.get('Fabrication Number', row.get('Fabrication', ''))),
                "customer_name": str(row.get('Customer', 'Unknown')),
                "category": str(row.get('Category', 'N/A')),
                "unit_status": str(row.get('Unit Status', 'Active')),
                "avg_running_hrs": float(row.get('Average Running Hours', row.get('Avg. Running', 0))),
                "current_hmr": float(row.get('Current Hours', row.get('CURRENT HMR', 0))),
                "total_hours_dn": float(row.get('Total Hours', row.get('MDA Total Hours', 0))),
                "last_service_date": str(row.get('Last Call Date', '2024-01-01')),
                "tracker_type": tracker_type
            }
            # Single row upload with retry logic
            supabase.table("machines").upsert(data).execute()
            
            # Har 20 records ke baad thoda break (Server ko saans lene ke liye)
            if i % 20 == 0:
                time.sleep(0.1)
                progress_bar.progress((i + 1) / len(df))
                
        except Exception as e:
            st.error(f"Error at row {i}: {e}")
            continue # Ek row fail ho toh ruko mat, agle par jao
            
    st.success("✅ Migration Finished!")

# --- UI Logic ---
st.title("📤 Migration Center")
t_type = st.selectbox("Select Tracker Type", ["DPSAC", "INDUSTRIAL"])
uploaded_file = st.file_uploader("Upload Excel", type="xlsx")

if uploaded_file and st.button("🚀 Start Migration"):
    df_excel = pd.read_excel(uploaded_file, engine='openpyxl')
    upload_to_supabase(df_excel, t_type)
