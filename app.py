import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# ==============================
# 🔐 CLOUD CONFIG (Secrets se linked)
# ==============================
URL = st.secrets["SUPABASE_URL"].strip()
KEY = st.secrets["SUPABASE_KEY"].strip()
supabase: Client = create_client(URL, KEY)

# ==============================
# ⚡ BATCH UPLOAD ENGINE (Fast & Stable)
# ==============================
def batch_sync(table_name, data_list, batch_size=400):
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
            
            # Progress bar update
            perc = min((i + batch_size) / total, 1.0)
            pb.progress(perc)
            status.text(f"✅ Synced: {success_count} / {total} records...")
            time.sleep(0.3) # Stability break
        except Exception as e:
            st.error(f"❌ Error at index {i}: {e}")
            break
            
    if success_count > 0:
        st.success(f"🏁 MISSION ACCOMPLISHED! {success_count} records are now live on Cloud.")
        st.balloons()

# ==============================
# 🏢 UI - MIGRATION CENTER
# ==============================
st.title("⚡ ELGi Cloud Sync - High Speed")
st.write("Connection Status: **🟢 LIVE**")

tab1, tab2, tab3 = st.tabs(["1. Master Data", "2. Active FOC", "3. Service History (22k)"])

with tab1:
    st.subheader("📤 Step 1: Sync Master Data")
    m_file = st.file_uploader("Upload Master_Data.xlsx", type="xlsx", key="m")
    t_type = st.selectbox("Type", ["DPSAC", "INDUSTRIAL"])
    if m_file and st.button("Sync Master"):
        df = pd.read_excel(m_file).fillna("N/A")
        m_list = []
        for _, row in df.iterrows():
            m_list.append({
                "fabrication_id": str(row.get('Fabrication Number', row.get('Fabrication', ''))).strip(),
                "customer_name": str(row.get('Customer', 'Unknown')),
                "category": str(row.get('Category', 'N/A')),
                "unit_status": str(row.get('Unit Status', 'Active')),
                "avg_running_hrs": float(row.get('Average Running Hours', row.get('Avg. Running', 0))),
                "current_hmr": float(row.get('Current Hours', row.get('CURRENT HMR', 0))),
                "total_hours_dn": float(row.get('Total Hours', row.get('MDA Total Hours', 0))),
                "last_service_date": str(pd.to_datetime(row.get('Last Call Date', '2024-01-01')).date()),
                "tracker_type": t_type
            })
        batch_sync("machines", m_list)

with tab3:
    st.subheader("🕒 Step 3: Sync 22,000+ History Records")
    s_file = st.file_uploader("Upload Service_Details.xlsx", type="xlsx", key="s")
    if s_file and st.button("🔥 Start Mega Sync"):
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

# Sidebar Status
if st.sidebar.button("📊 Real Cloud Count"):
    res_m = supabase.table("machines").select("fabrication_id", count="exact").execute()
    res_s = supabase.table("service_logs").select("id", count="exact").execute()
    st.sidebar.write(f"Machines: **{res_m.count}**")
    st.sidebar.write(f"Service Logs: **{res_s.count}**")
