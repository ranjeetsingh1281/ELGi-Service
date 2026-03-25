import streamlit as st
import pandas as pd
from supabase import create_client, Client
from io import BytesIO

# ==============================
# 🔐 SUPABASE CONFIG (Secrets Check)
# ==============================
if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
    URL = st.secrets["SUPABASE_URL"].strip()
    KEY = st.secrets["SUPABASE_KEY"].strip()
    supabase: Client = create_client(URL, KEY)
else:
    st.error("🚨 Missing Secrets in Streamlit Settings!")
    st.stop()

# ==============================
# 📂 DATA FUNCTIONS
# ==============================
@st.cache_data(ttl=600)
def fetch_data(tracker_type):
    try:
        res = supabase.table("machines").select("*").eq("tracker_type", tracker_type).execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"DB Error: {e}")
        return pd.DataFrame()

def upload_to_supabase(df, tracker_type):
    progress_bar = st.progress(0)
    total = len(df)
    for i, row in df.iterrows():
        data = {
            "fabrication_id": str(row.get('Fabrication Number', row.get('Fabrication', ''))),
            "customer_name": str(row.get('Customer', 'Unknown')),
            "category": str(row.get('Category', 'N/A')),
            "unit_status": str(row.get('Unit Status', 'Active')),
            "avg_running_hrs": float(row.get('Average Running Hours', row.get('Avg. Running', 0))),
            "current_hmr": float(row.get('Current Hours', row.get('CURRENT HMR', 0))),
            "total_hours_dn": float(row.get('Total Hours', row.get('MDA Total Hours', 0))),
            "last_service_date": str(row.get('Last Call Date', '2000-01-01')),
            "tracker_type": tracker_type
        }
        # Cloud mein insert/update (Upsert)
        supabase.table("machines").upsert(data).execute()
        progress_bar.progress((i + 1) / total)
    st.success(f"✅ {total} Records Migrated to Supabase!")

# ==============================
# 🏢 APP INTERFACE
# ==============================
st.sidebar.title("☁️ ELGi Cloud Admin")
nav = st.sidebar.radio("Navigation", ["Tracker Dashboard", "📤 Migration Center"])

if nav == "📤 Migration Center":
    st.title("📤 Excel to Cloud Migration")
    st.write("Purana Excel data yahan upload karke Supabase mein bhejein.")
    
    t_type = st.selectbox("Select Tracker Type", ["DPSAC", "INDUSTRIAL"])
    uploaded_file = st.file_uploader("Choose Excel File", type="xlsx")
    
    if uploaded_file and st.button("🚀 Start Migration to Cloud"):
        df_excel = pd.read_excel(uploaded_file, engine='openpyxl')
        upload_to_supabase(df_excel, t_type)

elif nav == "Tracker Dashboard":
    st.title("🛠️ ELGi Global Cloud Tracker")
    t_choice = st.selectbox("View Tracker", ["DPSAC", "INDUSTRIAL"])
    
    df_cloud = fetch_data(t_choice)
    if not df_cloud.empty:
        st.success(f"Linked to Supabase! Found {len(df_cloud)} machines.")
        st.dataframe(df_cloud, use_container_width=True)
        
        # --- Export Option ---
        st.download_button("📥 Export Cloud Data to Excel", 
                           df_cloud.to_csv(index=False).encode('utf-8'), 
                           f"{t_choice}_Cloud_Data.csv", "text/csv")
    else:
        st.warning("Database khali hai! Pehle 'Migration Center' mein jaakar Excel upload karein.")
