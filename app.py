import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# ==============================
# 🔐 CLOUD CONFIG
# ==============================
URL = st.secrets["SUPABASE_URL"].strip()
KEY = st.secrets["SUPABASE_KEY"].strip()
supabase: Client = create_client(URL, KEY)

# --- Number Cleaning Helper ---
def to_num(val):
    try:
        if pd.isna(val) or str(val).strip() == "": return 0.0
        # Sirf digits nikalna (agar kisi ne '120 hrs' likha ho toh bhi 120 utha lega)
        return float(''.join(c for c in str(val) if c.isdigit() or c == '.'))
    except:
        return 0.0

# ==============================
# ⚡ BATCH UPLOAD ENGINE
# ==============================
def batch_sync(table_name, data_list, batch_size=400):
    total = len(data_list)
    st.info(f"🚀 Syncing {total} records...")
    pb = st.progress(0)
    status = st.empty()
    
    for i in range(0, total, batch_size):
        batch = data_list[i : i + batch_size]
        try:
            supabase.table(table_name).upsert(batch).execute()
            current = min(i + batch_size, total)
            pb.progress(current / total)
            status.text(f"✅ Progress: {current} / {total}")
            time.sleep(0.2)
        except Exception as e:
            st.error(f"❌ Batch Error at {i}: {e}")
            break
    st.success("🏁 Done! Database updated.")

# ==============================
# 🏢 UI - MIGRATION
# ==============================
st.title("⚡ ELGi Cloud Sync - Error Fixed")

tab1, tab2 = st.tabs(["1. Master Data", "2. Service History"])

with tab1:
    m_file = st.file_uploader("Upload Master Data", type="xlsx")
    t_type = st.selectbox("Type", ["DPSAC", "INDUSTRIAL"])
    if m_file and st.button("Sync Master"):
        df = pd.read_excel(m_file).fillna(0)
        m_list = []
        for _, row in df.iterrows():
            m_list.append({
                "fabrication_id": str(row.get('Fabrication Number', row.get('Fabrication', ''))).strip(),
                "customer_name": str(row.get('Customer', 'Unknown')),
                "category": str(row.get('Category', 'N/A')),
                "unit_status": str(row.get('Unit Status', 'Active')),
                "avg_running_hrs": to_num(row.get('Average Running Hours', row.get('Avg. Running', 0))),
                "current_hmr": to_num(row.get('Current Hours', row.get('CURRENT HMR', 0))),
                "total_hours_dn": to_num(row.get('Total Hours', row.get('MDA Total Hours', 0))),
                "last_service_date": str(pd.to_datetime(row.get('Last Call Date', '2024-01-01')).date()),
                "tracker_type": t_type
            })
        batch_sync("machines", m_list)

with tab2:
    s_file = st.file_uploader("Upload Service Details (22k)", type="xlsx")
    if s_file and st.button("Sync Mega History"):
        df = pd.read_excel(s_file).fillna("N/A")
        srv_list = []
        for _, row in df.iterrows():
            srv_list.append({
                "fabrication_id": str(row.get('Fabrication Number', row.get('Fabrication', ''))).strip(),
                "service_date": str(pd.to_datetime(row.get('Visit Date', '2024-01-01')).date()),
                "description": f"Service: {str(row.get('Service Done', 'N/A'))}",
                "technician_name": str(row.get('Engineer', 'Admin'))
            })
        batch_sync("service_logs", srv_list)
