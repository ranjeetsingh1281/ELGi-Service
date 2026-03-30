import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime
from io import BytesIO

# ==============================
# 🔐 LOGIN SYSTEM
# ==============================
USER_DB = {
    "admin": {"pass": "admin123", "role": "all"},
    "user1": {"pass": "dpsac123", "role": "dpsac"},
    "user3": {"pass": "view456", "role": "viewer"}
}

if "d_login" not in st.session_state:
    st.title("🚜 ELGi DPSAC Tracker Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USER_DB and USER_DB[u]["pass"] == p:
            st.session_state["d_login"], st.session_state["d_user"], st.session_state["d_role"] = True, u, USER_DB[u]["role"]
            st.rerun()
        else: st.error("Invalid Credentials")
    st.stop()

# ==============================
# ⚙️ HELPERS
# ==============================
st.set_page_config(page_title="ELGi DPSAC Tracker Pro", layout="wide")

def fmt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try:
        val = pd.to_datetime(dt)
        return val.strftime('%d-%b-%y') if val.year > 1970 else "N/A"
    except: return "N/A"

def get_col_val(row, target):
    """Sahi column dhoond kar value nikalne ke liye flexible function"""
    target = str(target).strip().lower()
    for actual_col in row.index:
        if str(actual_col).strip().lower() == target:
            return row[actual_col]
    return "N/A"

@st.cache_data
def load_data():
    try:
        # File names MUST match exactly on GitHub
        m = pd.read_excel("Master_Data.xlsx", engine='openpyxl')
        f = pd.read_excel("Active_FOC.xlsx", engine='openpyxl')
        s = pd.read_excel("Service_Details.xlsx", engine='openpyxl')
        return m, f, s
    except Exception as e:
        st.error(f"File Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

master, foc, service = load_data()

# ==============================
# 💎 NAVIGATION
# ==============================
st.sidebar.title(f"👋 {st.session_state['d_user'].upper()}")
nav = ["Machine Search", "📦 Full FOC List", "⏳ Overdue Service"]
if st.session_state["d_role"] != "viewer": nav.append("📢 Automation Center")
choice = st.sidebar.radio("Navigation:", nav)

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()

# ==============================
# 💎 MAIN CONTENT
# ==============================
if master.empty:
    st.error("🚨 Master_Data.xlsx load nahi ho saki! GitHub check karein.")
    st.stop()

# Flexible Column Detection
cust_col = next((c for c in master.columns if 'customer' in str(c).lower()), master.columns[0])
fab_col = next((c for c in master.columns if 'fabrication' in str(c).lower()), master.columns[1])

if choice == "Machine Search":
    st.title("🛠️ DPSAC Machine Tracker")
    colA, colB = st.columns(2)
    sel_c = colA.selectbox("Select Customer", ["All"] + sorted(master[cust_col].astype(str).unique()))
    df_f = master if sel_c == "All" else master[master[cust_col] == sel_c]
    sel_f = colB.selectbox("Select Fabrication Number", ["Select"] + sorted(df_f[fab_col].astype(str).unique()))

    if sel_f != "Select":
        row = df_f[df_f[fab_col].astype(str) == str(sel_f)].iloc[0]
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.info("📋 Basic Info")
            h_val = get_col_val(row, "Current Hours") if get_col_val(row, "Current Hours") != "N/A" else get_col_val(row, "Current HMR")
            st.write(f"**Customer:** {row[cust_col]}")
            st.write(f"**HMR (Current):** `{h_val}`")
            st.write(f"**Last Call:** {fmt(get_col_val(row, 'Last Call Date'))}")

        # Parts mapping (Exact Column Match)
        p_map = {
            "OIL": {"repl": "OIL R DATE", "rem": "OIL Rem", "due": "OIL Due Date"},
            "AFC": {"repl": "AFC R DATE", "rem": "AFC Rem", "due": "AFC Due Date"},
            "AFE": {"repl": "AFE R DATE", "rem": "AFE Rem", "due": "AFE Due Date"},
            "MOF": {"repl": "MOF R DATE", "rem": "MOF Rem", "due": "MOF Due Date"},
            "ROF": {"repl": "ROF R DATE", "rem": "ROF Rem", "due": "ROF Due Date"},
            "AOS": {"repl": "AOS R DATE", "rem": "AOS Rem", "due": "AOS Due Date"},
            "RGT": {"repl": "RGT R DATE", "rem": "RGT Rem", "due": "RGT Due Date"},
            "1500": {"repl": "1500 R DATE", "rem": "1500 Rem", "due": "1500 Due Date"},
            "3000": {"repl": "3000 R DATE", "rem": "3000 Rem", "due": "3000 Due Date"}
        }

        with m2:
            st.info("🔧 History (R Date)")
            for lbl, k in p_map.items(): st.write(f"**{lbl}:** {fmt(get_col_val(row, k['repl']))}")
        with m3:
            st.info("⏳ Remaining (Hrs)")
            for lbl, k in p_map.items():
                val = get_col_val(row, k['rem'])
                icon = '🟢' if pd.notna(val) and str(val).replace('.','').replace('-','').isdigit() and float(val)>100 else '🔴'
                st.write(f"**{lbl}:** {icon} {val}")
        with m4:
            st.error("🚨 Next Due Date")
            for lbl, k in p_map.items(): st.write(f"**{lbl}:** {fmt(get_col_val(row, k['due']))}")

        # --- MACHINE LEVEL FOC & HISTORY ---
        st.divider()
        c_f, c_s = st.columns(2)
        with c_f:
            st.subheader("🎁 Machine FOC")
            f_fab_col = next((c for c in foc.columns if 'fabrication' in str(c).lower()), None)
            if f_fab_col:
                res_foc = foc[foc[f_fab_col].astype(str) == str(sel_f)]
                st.dataframe(res_foc, use_container_width=True) if not res_foc.empty else st.warning("No FOC entries.")
        with c_s:
            st.subheader("🕒 Service History")
            s_fab_col = next((c for c in service.columns if 'fabrication' in str(c).lower()), None)
            if s_fab_col:
                res_srv = service[service[s_fab_col].astype(str) == str(sel_f)]
                st.dataframe(res_srv, use_container_width=True) if not res_srv.empty else st.warning("No history entries.")

elif choice == "📦 Full FOC List":
    st.dataframe(foc, use_container_width=True)

elif choice == "⏳ Overdue Service":
    over_c = next((c for c in master.columns if 'overdue' in str(c).lower() or 'red' in str(c).lower()), None)
    if over_c:
        st.dataframe(master[master[over_c] > 0], use_container_width=True)
    else: st.warning("Overdue column nahi mila.")
