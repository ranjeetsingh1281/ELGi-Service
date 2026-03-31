import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime
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
st.set_page_config(page_title="ELGi DPSAC Tracker Pro", layout="wide")

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

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
# 📊 SIDEBAR METRICS (Fixed Layout)
# ==============================
st.sidebar.title(f"👋 {st.session_state['d_user'].upper()}")

if not master.empty:
    st.sidebar.divider()
    st.sidebar.markdown("### 📊 Dashboard Metrics")
    
    # Total Units
    st.sidebar.write(f"**Total Units:** {len(master)}")

    # Commissioned Box
    us_col = next((c for c in master.columns if 'unit status' in c.lower()), None)
    comm_count = len(master[master[us_col].astype(str).str.contains('Commissioned', case=False)]) if us_col else 0
    st.sidebar.info(f"✅ Commissioned: {comm_count}")

    # Due Dates Calculation
    due_col = next((c for c in master.columns if 'oil due' in c.lower()), None)
    if due_col:
        master[due_col] = pd.to_datetime(master[due_col], errors='coerce')
        now = datetime.now()
        curr_m = len(master[master[due_col].dt.month == now.month])
        next_m = len(master[master[due_col].dt.month == (now.month % 12) + 1])
        
        st.sidebar.warning(f"📅 Current Month Due: {curr_m}")
        st.sidebar.success(f"🗓️ Next Month Due: {next_m}")

st.sidebar.divider()
# --- ERROR FIX: Variable name is 'choice' now ---
choice = st.sidebar.radio("Navigation:", ["Machine Search", "📦 FOC List", "⏳ Overdue Service", "📢 Automation"])

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()

# ==============================
# 📦 FOC LIST (Filtered Columns)
# ==============================
if choice == "📦 FOC List":
    st.title("📦 DPSAC FOC Tracking List")
    
    required_columns = [
        "Created On", "FOC Number", "Work Order Number", "Customer Name", 
        "FOC Type", "FOC Category", "FOC Status", "Created By", "Owner", 
        "MODEL", "FABRICATION NO.", "MANUAL CHALLAN NO.", 
        "DEALER INVOICE NO./ DATE", "ELGI IVOICE NO.1", 
        "MATERIAL RECEIVED (Y/N)/ DATE", "REMARKS", 
        "Failure Material Details", "Part Code", "Qty"
    ]
    
    # Exact Column Filter
    available_cols = [c for c in required_columns if c in foc.columns]
    
    if not foc.empty:
        search_id = st.text_input("🔍 Search by FOC or Fab Number:")
        display_foc = foc[available_cols]
        
        if search_id:
            display_foc = display_foc[display_foc.astype(str).apply(lambda x: x.str.contains(search_id, case=False)).any(axis=1)]
        
        st.dataframe(display_foc, use_container_width=True)
        st.download_button("📥 Export FOC Report", to_excel(display_foc), "FOC_Report.xlsx")
    else:
        st.warning("FOC Data load nahi ho saka.")

# ==============================
# 🛠️ MACHINE SEARCH & OTHERS
# ==============================
elif choice == "Machine Search":
    st.title("🛠️ Detailed Machine Search")
    # ... baki search logic same rahega ...
