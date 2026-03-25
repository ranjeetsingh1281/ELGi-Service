import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# ==============================
# 🔐 SUPABASE CONFIG (Auto-Correction)
# ==============================
if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
    # URL aur Key se unwanted spaces aur extra slashes hatana
    URL = st.secrets["SUPABASE_URL"].strip().rstrip('/')
    KEY = st.secrets["SUPABASE_KEY"].strip()
    
    try:
        supabase: Client = create_client(URL, KEY)
    except Exception as e:
        st.error(f"❌ Initialization Error: {e}")
        st.stop()
else:
    st.error("🚨 Secrets Missing! Streamlit Settings > Secrets mein URL aur KEY daalein.")
    st.stop()

# ==============================
# ⚡ BATCH SYNC ENGINE (Retry & Stability)
# ==============================
def batch_sync(table_name, data_list, batch_size=300):
    total = len(data_list)
    st.info(f"🚀 Starting Sync for {total} records...")
    pb = st.progress(0)
    status = st.empty()
    success_count = 0

    for i in range(0, total, batch_size):
        batch = data_list[i : i + batch_size]
        try:
            # Cloud Bulk Insert
            supabase.table(table_name).upsert(batch).execute()
            success_count += len(batch)
            
            # UI Update
            current_progress = min((i + batch_size) / total, 1.0)
            pb.progress(current_progress)
            status.text(f"✅ Progress: {success_count} / {total} records synced...")
            
            # Thoda sa delay connection stable rakhne ke liye
            time.sleep(0.4)
            
        except Exception as e:
            st.error(f"❌ Batch Error at index {i}: {e}")
            st.warning("💡 Tip: Check if Supabase URL in Secrets is 100% correct.")
            break 
            
    if success_count > 0:
        st.success(f"🏁 Mission Accomplished! {success_count} records are now in Cloud.")

# ==============================
# 🏢 UI - MIGRATION CENTER
# ==============================
st.title("⚡ ELGi Bullet-Proof Cloud Sync")
st.write("Specialized for 22,000+ Service Records 🕒")

# Sidebar for DB Status
if st.sidebar.button("📊 Real-Time Cloud Count"):
    try:
        res = supabase.table("service_logs").select("id", count="exact").execute()
        st.sidebar.metric("Records in Supabase", res.count)
    except Exception:
        st.sidebar.error("Could not fetch count. Check URL.")

# Main Sync Section
s_file = st.file_uploader("Upload Service_Details.xlsx", type="xlsx")

if s_file and st.button("🔥 Start High-Speed Sync"):
    try:
        with st.spinner("Reading Excel... Please wait."):
            df = pd.read_excel(s_file).fillna("N/A")
            
        srv_list = []
        # Mapping Excel to Supabase Schema
        for _, row in df.iterrows():
            srv_list.append({
                "fabrication_id": str(row.get('Fabrication Number', row.get('Fabrication', ''))).strip(),
                "service_date": str(pd.to_datetime(row.get('Visit Date', '2024-01-01')).date()),
                "description": f"Service: {str(row.get('Service Done', 'N/A'))}",
                "technician_name": str(row.get('Engineer', 'Admin'))
            })
        
        if srv_list:
            batch_sync("service_logs", srv_list)
        else:
            st.warning("Excel file is empty or headers don't match.")
            
    except Exception as e:
        st.error(f"❌ Excel Processing Error: {e}")
