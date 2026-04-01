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

def fmt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try: return pd.to_datetime(dt).strftime('%d-%b-%y')
    except: return "N/A"

def smart_get(row, keywords):
    for col in row.index:
        col_clean = str(col).strip().lower().replace("-", "").replace("_", "").replace(" ", "")
        
        if all(k.lower().replace(" ", "") in col_clean for k in keywords):
            val = row[col]
            return val if pd.notna(val) else "N/A"
    
    return "N/A"
    """Multiple keywords se sahi column dhoond kar value nikalne ka function"""
   
@st.cache_data
def load_all_data():
    try:
        m = pd.read_excel("Master_Data.xlsx", engine='openpyxl')
        f = pd.read_excel("Active_FOC.xlsx", engine='openpyxl')
        s = pd.read_excel("Service_Details.xlsx", engine='openpyxl')
        # Standardize: column names se extra space hatana
        for d in [m, f, s]: d.columns = [str(c).strip() for c in d.columns]
        return m, f, s
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

master, foc, service = load_all_data()

# ==============================
# 📊 SIDEBAR METRICS
# ==============================
st.sidebar.title(f"👋 {st.session_state['d_user'].upper()}")

if not master.empty:
    st.sidebar.divider()
    st.sidebar.markdown("### 📊 Dashboard Metrics")
    st.sidebar.write(f"**Total Units:** {len(master)}")

    # Commissioned Box
    us_col = next((c for c in master.columns if 'unit status' in str(c).lower()), None)
    comm_count = len(master[master[us_col].astype(str).str.contains('Commissioned', case=False)]) if us_col else 0
    st.sidebar.info(f"✅ Commissioned: {comm_count}")

    # Due Dates Calculation
    due_col = next((c for c in master.columns if 'oil due' in str(c).lower()), None)
    if due_col:
        master[due_col] = pd.to_datetime(master[due_col], errors='coerce')
        now = datetime.now()
        curr_m = len(master[master[due_col].dt.month == now.month])
        next_m = len(master[master[due_col].dt.month == (now.month % 12) + 1])
        st.sidebar.warning(f"📅 Current Month Due: {curr_m}")
        st.sidebar.success(f"🗓️ Next Month Due: {next_m}")

st.sidebar.divider()
choice = st.sidebar.radio("Navigation:", ["Machine Search", "📦 FOC List", "⏳ Overdue Service", "📢 Automation"])

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()

# ==============================
# 🛠️ MACHINE SEARCH (Ultra Flexible Fix)
# ==============================
if choice == "Machine Search":
    st.title("🛠️ Detailed Machine Search")
    
    if master.empty:
        st.error("Master_Data.xlsx load nahi ho saki!")
        st.stop()

    cust_col = next((c for c in master.columns if 'customer' in str(c).lower()), master.columns[0])
    fab_col = next((c for c in master.columns if 'fabrication' in str(c).lower()), master.columns[1])

    c1, c2 = st.columns(2)
    sel_c = c1.selectbox("Select Customer", ["All"] + sorted(master[cust_col].astype(str).unique()))
    df_f = master if sel_c == "All" else master[master[cust_col] == sel_c]
    sel_f = c2.selectbox("Select Fabrication Number", ["Select"] + sorted(df_f[fab_col].astype(str).unique()))

    if sel_f != "Select":
        row = df_f[df_f[fab_col].astype(str) == str(sel_f)].iloc[0]
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.info("📋 Basic Info")
            hmr = smart_get(row, ["current", "hmr"])
            if hmr == "N/A": hmr = smart_get(row, ["current", "hours"])
            st.write(f"**Customer:** {row[cust_col]}")
            st.write(f"**HMR:** `{hmr}`")
            st.write(f"**Last Call:** {fmt(smart_get(row, ['last', 'call']))}")

        # Parts mapping
        parts_map = {
            "OIL": ["oil", "r"],
            "AFC": ["afc", "r"],
            "AFE": ["afe", "r"],
            "MOF": ["mof", "r"],
            "ROF": ["rof", "r"],
            "AOS": ["aos", "r"],
            "RGT": ["grease", "r"],
            "1500": ["1500", "r"],
            "3000": ["3000", "r"]
}
        with m2:
            st.info("🔧 History (R Date)")
            for p in parts: st.write(f"**{p}:** {fmt(smart_get(row, [p, 'r date']))}")
        with m3:
            st.info("⏳ Remaining (Hrs)")
            for p in parts:
                val = smart_get(row, [p, 'rem'])
                icon = '🟢' if pd.notna(val) and str(val).replace('.','').replace('-','').isdigit() and float(val)>100 else '🔴'
                st.write(f"**{p}:** {icon} {val}")
        with m4:
            st.error("🚨 Next Due Date")
            for p in parts: st.write(f"**{p}:** {fmt(smart_get(row, [p, 'due']))}")

        # Deep Links
        st.divider()
        low1, low2 = st.columns(2)
        with low1:
            st.subheader("🎁 Machine FOC")
            f_fab = next((c for c in foc.columns if 'fabrication' in str(c).lower()), foc.columns[0])
            st.dataframe(foc[foc[f_fab].astype(str) == str(sel_f)], use_container_width=True)
        with low2:
            st.subheader("🕒 Service History")
            s_fab = next((c for c in service.columns if 'fabrication' in str(c).lower()), service.columns[0])
            st.dataframe(service[service[s_fab].astype(str) == str(sel_f)], use_container_width=True)

# ==============================
# 📦 FOC LIST (Filtered Columns)
# ==============================
elif choice == "📦 FOC List":
    st.title("📦 DPSAC FOC Tracking List")
    req_cols = ["Created On", "FOC Number", "Work Order Number", "Customer Name", "FOC Status", "FABRICATION NO.", "Part Code", "Qty"]
    available_cols = [c for c in req_cols if c in foc.columns]
    if not foc.empty:
        st.dataframe(foc[available_cols], use_container_width=True)
    else: st.warning("No FOC Data.")

# ==============================
# ⏳ OVERDUE SERVICE
# ==============================
elif choice == "⏳ Overdue Service":
    st.title("⏳ Overdue List")
    over_c = next((c for c in master.columns if 'overdue' in str(c).lower()), None)
    if over_c:
        master[over_c] = pd.to_numeric(master[over_c], errors='coerce').fillna(0)
        st.dataframe(master[master[over_c] > 0], use_container_width=True)

# ==============================
# 📢 AUTOMATION
# ==============================
elif choice == "📢 Automation":
    st.title("📢 Automation Center")
    msg = st.text_area("WA Message:", "ELGi Service Alert!")
    wa_link = f"https://wa.me/917061158953?text={urllib.parse.quote(msg)}"
    st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color:#25D366; color:white; padding:12px; border-radius:5px; width:100%; cursor:pointer; font-weight:bold;">📱 Send WhatsApp</button></a>', unsafe_allow_html=True)
