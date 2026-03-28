import streamlit as st
import pandas as pd
import os
import urllib.parse
from io import BytesIO

# ==============================
# 🔐 LOGIN SYSTEM (DPSAC)
# ==============================
USER_DB = {
    "admin": "admin123",
    "dpsac_user": "dpsac123",
    "viewer": "view456"
}

def login():
    st.title("🚜 ELGi DPSAC Tracker Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USER_DB and USER_DB[u] == p:
            st.session_state["dpsac_login"] = True
            st.rerun()
        else: st.error("Invalid Credentials")

if "dpsac_login" not in st.session_state:
    login(); st.stop()

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

def get_val(row, df_columns, target_name):
    target = str(target_name).strip().lower()
    for col in df_columns:
        if str(col).strip().lower() == target: return row[col]
    return "N/A"

# ==============================
# 📂 DATA LOADING
# ==============================
@st.cache_data
def load_data():
    try:
        m = pd.read_excel("Master_Data.xlsx", engine='openpyxl')
        f = pd.read_excel("Active_FOC.xlsx", engine='openpyxl')
        s = pd.read_excel("Service_Details.xlsx", engine='openpyxl')
        for d in [m, f, s]: d.columns = [str(c).strip() for c in d.columns]
        return m, f, s
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

master, foc, service = load_data()

# ==============================
# 💎 DPSAC SEARCH ENGINE
# ==============================
st.title("🛠️ DPSAC Tracker Pro")
cust_col = next((c for c in master.columns if 'Customer' in str(c)), master.columns[0])
fab_col = next((c for c in master.columns if 'Fabrication' in str(c)), master.columns[1])

t1, t2, t3 = st.tabs(["Machine Search", "📦 Full FOC", "⏳ Service Pending"])

with t1:
    colA, colB = st.columns(2)
    sel_c = colA.selectbox("Select Customer", ["All"] + sorted(master[cust_col].astype(str).unique()))
    df_f = master if sel_c == "All" else master[master[cust_col] == sel_c]
    sel_f = colB.selectbox("Select Fabrication Number", ["Select"] + sorted(df_f[fab_col].astype(str).unique()))

    if sel_f != "Select":
        row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]
        cols = master.columns
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.info("📋 Info")
            st.write(f"**Customer:** {row[cust_col]}")
            st.write(f"**HMR:** `{row.get('Current Hours', row.get('Current HMR', 0))}`")
            st.write(f"**Last Call:** {fmt(row.get('Last Call Date'))}")

        # DPSAC Specific Parts
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
            st.info("🔧 History")
            for lbl, k in p_map.items(): st.write(f"**{lbl}:** {fmt(get_val(row, cols, k['repl']))}")
        with m3:
            st.info("⏳ Remaining")
            for lbl, k in p_map.items():
                val = get_val(row, cols, k['rem'])
                icon = '🟢' if pd.notna(val) and str(val).replace('.','').replace('-','').isdigit() and float(val)>100 else '🔴'
                st.write(f"**{lbl}:** {icon} {val}")
        with m4:
            st.error("🚨 Due Date")
            for lbl, k in p_map.items(): st.write(f"**{lbl}:** {fmt(get_val(row, cols, k['due']))}")

        st.divider()
        # History & FOC
        c1, c2 = st.columns(2)
        with c1: st.subheader("🎁 FOC"); st.dataframe(foc[foc[next(iter(foc.columns))].astype(str) == sel_f])
        with c2: st.subheader("🕒 History"); st.dataframe(service[service[next(iter(service.columns))].astype(str) == sel_f])
