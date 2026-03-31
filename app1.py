import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime, timedelta
from io import BytesIO

# ==============================
# 🔐 LOGIN SYSTEM
# ==============================
USER_DB = {"admin": "admin123", "user1": "dpsac123", "view": "view456"}

if "d_login" not in st.session_state:
    st.title("🚜 ELGi DPSAC Tracker Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USER_DB and USER_DB[u] == p:
            st.session_state["d_login"], st.session_state["d_user"] = True, u
            st.rerun()
        else: st.error("Invalid Credentials")
    st.stop()

# ==============================
# ⚙️ CONFIG & HELPERS
# ==============================
st.set_page_config(page_title="ELGi DPSAC Tracker", layout="wide")

def fmt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try: return pd.to_datetime(dt).strftime('%d-%b-%y')
    except: return "N/A"

@st.cache_data
def load_all_data():
    try:
        m = pd.read_excel("Master_Data.xlsx", engine='openpyxl')
        f = pd.read_excel("Active_FOC.xlsx", engine='openpyxl')
        s = pd.read_excel("Service_Details.xlsx", engine='openpyxl')
        for d in [m, f, s]: d.columns = [str(c).strip() for c in d.columns]
        return m, f, s
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

master, foc, service = load_all_data()

# ==============================
# 📊 SIDEBAR KPI COUNTERS (NEW UPDATE)
# ==============================
st.sidebar.title(f"👋 {st.session_state['d_user'].upper()}")

if not master.empty:
    st.sidebar.divider()
    st.sidebar.subheader("📊 Dashboard Metrics")
    
    # 1. Unit Status Count (Assuming 'Unit Status' column exists)
    us_col = next((c for c in master.columns if 'unit status' in c.lower()), None)
    if us_col:
        st.sidebar.write(f"**Total Units:** {len(master)}")
        st.sidebar.info(f"✅ Commissioned: {len(master[master[us_col].astype(str).str.contains('Commissioned', case=False)])}")

    # 2. Overdue Count
    od_col = next((c for c in master.columns if 'overdue' in c.lower()), None)
    if od_col:
        od_count = len(master[pd.to_numeric(master[od_col], errors='coerce').fillna(0) > 0])
        st.sidebar.error(f"🚨 Overdue Count: {od_count}")

    # 3. Current Month Due Count & 4. Next Month Due
    # Hum 'OIL Due Date' ko standard maante hain calculation ke liye
    due_col = next((c for c in master.columns if 'oil due' in c.lower()), None)
    if due_col:
        master[due_col] = pd.to_datetime(master[due_col], errors='coerce')
        now = datetime.now()
        curr_month = master[master[due_col].dt.month == now.month]
        next_month = master[master[due_col].dt.month == (now.month % 12) + 1]
        st.sidebar.warning(f"📅 Current Month Due: {len(curr_month)}")
        st.sidebar.success(f"🗓️ Next Month Due: {len(next_month)}")

st.sidebar.divider()
nav = st.sidebar.radio("Navigation:", ["Machine Search", "📦 FOC List", "⏳ Overdue Service", "📢 Automation"])

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()

# ==============================
# 💎 MAIN CONTENT - DPSAC FOC LIST (COLUMNS FILTERED)
# ==============================
if choice == "📦 FOC List":
    st.title("📦 DPSAC FOC Tracking List")
    
    # --- BOSS, ye hain aapke requested columns ---
    required_columns = [
        "Created On", "FOC Number", "Work Order Number", "Customer Name", 
        "FOC Type", "FOC Category", "FOC Status", "Created By", "Owner", 
        "MODEL", "FABRICATION NO.", "MANUAL CHALLAN NO.", 
        "DEALER INVOICE NO./ DATE", "ELGI IVOICE NO.1", 
        "MATERIAL RECEIVED (Y/N)/ DATE", "REMARKS", 
        "Failure Material Details", "Part Code", "Qty"
    ]
    
    # Filtering columns that exist in the excel
    available_cols = [c for c in required_columns if c in foc.columns]
    
    if not foc.empty:
        # Search Box for FOC List
        search_foc = st.text_input("🔍 Search by FOC or Fabrication No:")
        display_foc = foc[available_cols]
        
        if search_foc:
            display_foc = display_foc[display_foc.astype(str).apply(lambda x: x.str.contains(search_foc, case=False)).any(axis=1)]
        
        st.dataframe(display_foc, use_container_width=True)
        st.download_button("📥 Download Filtered FOC", display_foc.to_csv(index=False), "FOC_Report.csv")
    else:
        st.warning("FOC Data nahi mila!")

# --- MACHINE SEARCH SECTION ---
elif choice == "Machine Search":
    st.title("🛠️ Machine Detailed Lookup")
    # (Purana logic jisme m1, m2, m3, m4 grid hai)
    # ... code continues ...
