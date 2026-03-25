import streamlit as st
import pandas as pd
import time
from supabase import create_client, Client

# ==============================
# 🔐 SUPABASE CONFIG
# ==============================
if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
    URL = st.secrets["SUPABASE_URL"].strip().rstrip('/')
    KEY = st.secrets["SUPABASE_KEY"].strip()
    supabase: Client = create_client(URL, KEY)
else:
    st.error("🚨 Secrets missing in Streamlit Settings!")
    st.stop()

# ==============================
# ⚡ BATCH UPLOAD ENGINE (Anti-Timeout)
# ==============================
def batch_sync(table_name, final_list, batch_size=500):
    total = len(final_list)
    st.info(f"🚀 Starting Batch Upload: {total} records to {table_name}")
    pb = st.progress(0)
    status = st.empty()

    for i in range(0, total, batch_size):
        batch = final_list[i : i + batch_size]
        try:
            # Bulk Insert into Supabase
            supabase.table(table_name).upsert(batch).execute()
            
            # Progress Update
            current_progress = min((i + batch_size) / total, 1.0)
            pb.progress(current_progress)
            status.text(f"✅ Syncing... {min(i + batch_size, total)} / {total}")
            
            # Chota sa break taaki connection stable rahe
            time.sleep(0.2)
        except Exception as e:
            st.error(f"❌ Error at index {i}: {e}")
            break
            
    st.success(f"🏁 Mission Accomplished! {total} records synced to {table_name}.")

# ==============================
# 🏢 UI - MIGRATION CENTER
# ==============================
st.title("⚡ ELGi High-Speed Cloud Sync")
st.write("22,000+ records ke liye Batch Mode active hai. 🛠️")

tab1, tab2 = st.tabs(["📦 Sync Active FOC", "🕒 Sync Service Details"])

with tab1:
    st.subheader("📦 Upload Active_FOC.xlsx")
    f_file = st.file_uploader("Choose FOC File", type="xlsx", key="foc_up")
    if f_file and st.button("🚀 Sync FOC to Cloud"):
        df = pd.read_excel(f_file).fillna("N/A")
        foc_list = []
        for _, row in df.iterrows():
            foc_list.append({
                "fabrication_id": str(row.get('Fabrication Number', row.get('Fabrication', ''))).strip(),
                "description": f"FOC: {str(row.get('Description', row.get('Item', 'N/A')))}",
                "service_date": str(pd.to_datetime(row.get('Date', '2024-01-01')).date())
            })
        batch_sync("service_logs", foc_list)

with tab2:
    st.subheader("🕒 Upload Service_Details.xlsx")
    s_file = st.file_uploader("Choose Service Details File", type="xlsx", key="srv_up")
    if s_file and st.button("🔥 Sync 22k+ Records"):
        df = pd.read_excel(s_file).fillna("N/A")
        srv_list = []
        for _, row in df.iterrows():
            srv_list.append({
                "fabrication_id": str(row.get('Fabrication Number', row.get('Fabrication', ''))).strip(),
                "service_date": str(pd.to_datetime(row.get('Visit Date', '2024-01-01')).date()),
                "description": f"Service: {str(row.get('Service Done', 'N/A'))}",
                "technician_name": str(row.get('Engineer', 'Admin'))
            })
        # Running High-Speed Batch Upload
        batch_sync("service_logs", srv_list)

# --- Sidebar Counter ---
if st.sidebar.button("📊 Check Cloud Status"):
    res = supabase.table("service_logs").select("id", count="exact").execute()
    st.sidebar.write(f"**Total Records in Cloud:** {res.count}")
