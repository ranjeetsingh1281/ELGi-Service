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
            st.session_state["d_login"] = True
            st.session_state["d_user"] = u
            st.session_state["d_role"] = USER_DB[u]["role"]
            st.rerun()
        else:
            st.error("Invalid Credentials")
    st.stop()

# ==============================
# ⚙️ CONFIG & HELPERS
# ==============================
st.set_page_config(page_title="ELGi DPSAC Tracker", layout="wide")

def fmt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try:
        val = pd.to_datetime(dt)
        return val.strftime('%d-%b-%y') if val.year > 1970 else "N/A"
    except: return "N/A"

@st.cache_data
def load_excel_files():
    try:
        m = pd.read_excel("Master_Data.xlsx", engine='openpyxl')
        f = pd.read_excel("Active_FOC.xlsx", engine='openpyxl')
        s = pd.read_excel("Service_Details.xlsx", engine='openpyxl')
        for d in [m, f, s]: d.columns = [str(c).strip() for c in d.columns]
        return m, f, s
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

master, foc, service = load_excel_files()

# ==============================
# 🏢 SIDEBAR NAVIGATION
# ==============================
st.sidebar.title(f"👋 {st.session_state['d_user'].upper()}")
nav_list = ["Machine Search", "📦 Full FOC List", "⏳ Overdue Service"]
if st.session_state["d_role"] != "viewer":
    nav_list.append("📢 Automation Center")

choice = st.sidebar.radio("Navigation:", nav_list)

if st.sidebar.button("Logout"):
    del st.session_state["d_login"]
    st.rerun()

# ==============================
# 💎 CONTENT LOGIC
# ==============================
if master.empty:
    st.error("🚨 Master_Data.xlsx load nahi ho saki. File name check karein.")
    st.stop()

# Auto-detect columns
cust_col = next((c for c in master.columns if 'Customer' in str(c)), master.columns[0])
fab_col = next((c for c in master.columns if 'Fabrication' in str(c)), master.columns[1])

if choice == "Machine Search":
    st.title("🛠️ Machine Tracker")
    colA, colB = st.columns(2)
    sel_c = colA.selectbox("Select Customer", ["All"] + sorted(master[cust_col].astype(str).unique()))
    df_f = master if sel_c == "All" else master[master[cust_col] == sel_c]
    sel_f = colB.selectbox("Select Fabrication Number", ["Select"] + sorted(df_f[fab_col].astype(str).unique()))

    if sel_f != "Select":
        row = df_f[df_f[fab_col].astype(str) == str(sel_f)].iloc[0]
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.info("📋 Basic Info")
            st.write(f"**Customer:** {row[cust_col]}")
            st.write(f"**HMR:** `{row.get('Current Hours', 'N/A')}`")
        
        # Parts Lookup
        p_map = {"OIL": "OIL R DATE", "AFC": "AFC R DATE", "AFE": "AFE R DATE", "AOS": "AOS R DATE"}
        with m2:
            st.info("🔧 History")
            for k, v in p_map.items(): st.write(f"**{k}:** {fmt(row.get(v))}")
        
        st.divider()
        st.subheader("🕒 Service History")
        s_fab = next((c for c in service.columns if 'Fabrication' in str(c)), None)
        if s_fab:
            st.dataframe(service[service[s_fab].astype(str) == str(sel_f)], use_container_width=True)

elif choice == "📦 Full FOC List":
    st.title("📦 Active FOC List")
    st.dataframe(foc, use_container_width=True)

elif choice == "⏳ Overdue Service":
    st.title("⏳ Service Pending")
    over_c = next((c for c in master.columns if 'Overdue' in str(c)), None)
    if over_c: st.dataframe(master[master[over_c] > 0], use_container_width=True)

elif choice == "📢 Automation Center":
    st.title("📢 Notifications")
    st.write("WhatsApp broadcast link ready...")
