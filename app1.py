import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime
from io import BytesIO

# ==============================
# 🔐 ROLE-BASED LOGIN SYSTEM
# ==============================
USER_DB = {
    "admin": {"pass": "admin123", "role": "all"},
    "user1": {"pass": "dpsac123", "role": "dpsac"},
    "user3": {"pass": "view456", "role": "viewer"}
}

def login():
    st.title("🚜 ELGi DPSAC Tracker Login")
    u = st.text_input("Username", key="login_user")
    p = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        if u in USER_DB and USER_DB[u]["pass"] == p:
            st.session_state["d_login"] = True
            st.session_state["d_user"] = u
            st.session_state["d_role"] = USER_DB[u]["role"]
            st.rerun()
        else:
            st.error("Invalid Username or Password")

if "d_login" not in st.session_state:
    login()
    st.stop()

# ==============================
# ⚙️ CONFIG & HELPERS
# ==============================
st.set_page_config(page_title="ELGi DPSAC Tracker Pro", layout="wide")

def fmt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try:
        val = pd.to_datetime(dt)
        return val.strftime('%d-%b-%y') if val.year > 1970 else "N/A"
    except: return "N/A"

def get_val(row, df_columns, target_name):
    """Case-insensitive and space-safe column lookup"""
    target = str(target_name).strip().lower()
    for col in df_columns:
        if str(col).strip().lower() == target:
            return row[col]
    return "N/A"

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# ==============================
# 📂 DATA LOADING (Direct Excel)
# ==============================
@st.cache_data
def load_dpsac_data():
    try:
        # File names must match exactly on GitHub
        m = pd.read_excel("Master_Data.xlsx", engine='openpyxl')
        f = pd.read_excel("Active_FOC.xlsx", engine='openpyxl')
        s = pd.read_excel("Service_Details.xlsx", engine='openpyxl')
        
        # Standardize column names
        for d in [m, f, s]:
            if not d.empty:
                d.columns = [str(c).strip() for c in d.columns]
        return m, f, s
    except Exception as e:
        st.error(f"Error loading files: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

master, foc, service = load_dpsac_data()

# ==============================
# 🏢 NAVIGATION & SIDEBAR
# ==============================
role = st.session_state["d_role"]
st.sidebar.title(f"👋 {st.session_state['d_user'].upper()}")

nav_options = ["Machine Search", "📦 Full FOC List", "⏳ Overdue Service"]
if role != "viewer":
    nav_options.append("📢 Automation Center")

choice = st.sidebar.radio("Navigation:", nav_options)

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ==============================
# 💎 MAIN ENGINE
# ==============================
if master.empty:
    st.warning("🚨 'Master_Data.xlsx' nahi mili ya khali hai. GitHub check karein.")
    st.stop()

# Auto-detect critical columns
cust_col = next((c for c in master.columns if 'Customer' in str(c)), master.columns[0])
fab_col = next((c for c in master.columns if 'Fabrication' in str(c)), master.columns[1])
