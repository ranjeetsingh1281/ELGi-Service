import streamlit as st
import pandas as pd
import os
import urllib.parse
from io import BytesIO

# ==============================
# 🔐 LOGIN SYSTEM (INDUSTRIAL)
# ==============================
USER_DB = {
    "admin": {"pass": "admin123", "role": "all"},
    "user2": {"pass": "ind123", "role": "industrial"},
    "user3": {"pass": "view456", "role": "viewer"}
}

def login():
    st.title("🏗️ ELGi INDUSTRIAL Tracker Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USER_DB and USER_DB[u]["pass"] == p:
            st.session_state["i_login"], st.session_state["i_role"] = True, USER_DB[u]["role"]
            st.rerun()
        else: st.error("Invalid Credentials")

if "i_login" not in st.session_state:
    login(); st.stop()

# ==============================
# ⚙️ HELPERS
# ==============================
st.set_page_config(page_title="ELGi Industrial Tracker", layout="wide")

def fmt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try:
        val = pd.to_datetime(dt)
        return val.strftime('%d-%b-%y') if val.year > 1970 else "N/A"
    except: return "N/A"

# ==============================
# 📂 DATA LOADING
# ==============================
@st.cache_data
def load_data():
    try:
        m = pd.read_excel("Master_OD_Data.xlsx", engine='openpyxl')
        f = pd.read_excel("Active_FOC.xlsx", engine='openpyxl')
        s = pd.read_excel("Service_Details.xlsx", engine='openpyxl')
        for d in [m, f, s]: d.columns = [str(c).strip() for c in d.columns]
        return m, f, s
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

master, foc, service = load_data()

# ==============================
# 💎 INDUSTRIAL ENGINE
# ==============================
st.title("🛠️ INDUSTRIAL Tracker Pro")
role = st.session_state["i_role"]

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()

nav = ["Machine Search", "📦 Full FOC", "⏳ Overdue Service"]
if role != "viewer": nav.append("📢 Automation Center")
choice = st.sidebar.radio("Navigation:", nav)

if choice == "Machine Search":
    cust_col = next((c for c in master.columns if 'Customer' in c), master.columns[0])
    fab_col = next((c for c in master.columns if 'Fabrication' in c), master.columns[1])
    
    col1, col2 = st.columns(2)
    sel_c = col1.selectbox("Select Customer", ["All"] + sorted(master[cust_col].astype(str).unique()))
    df_f = master if sel_c == "All" else master[master[cust_col] == sel_c]
    sel_f = col2.selectbox("Select Fabrication Number", ["Select"] + sorted(df_f[fab_col].astype(str).unique()))

    if sel_f != "Select":
        row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            st.info("📋 Basic Info")
            st.write(f"**Customer:** {row[cust_col]}")
            st.write(f"**Current HMR:** `{row.get('CURRENT HMR', 0)}`")
            st.write(f"**Last Call:** {fmt(row.get('Last Call Date'))}")

        p_map = {
            "OIL": {"repl": "MDA Oil R Date", "rem": "OIL Rem. HMR Till date", "due": "Oil R Date"},
            "AF": {"repl": "MDA AF R Date", "rem": "AF Rem. HMR Till date", "due": "AF R Date"},
            "OF": {"repl": "MDA OF R Date", "rem": "OF Rem. HMR Till date", "due": "OF R Date"},
            "AOS": {"repl": "MDA AOS R Date", "rem": "AOS Rem. HMR Till date", "due": "AOS R Date"},
            "RGT": {"repl": "MDA RGT R Date", "rem": "RGT Rem. HMR Till date", "due": "RGT R Date"},
            "VK": {"repl": "MDA Valvekit R Date", "rem": "VK Rem. HMR Till date", "due": "Valvekit R Date"},
            "PF": {"repl": "MDA PF R DATE", "rem": "PF Rem", "due": "PF R DATE"},
            "FF": {"repl": "MDA FF R DATE", "rem": "FF Rem", "due": "FF R DATE"},
            "CF": {"repl": "MDA CF R DATE", "rem": "CF Rem", "due": "CF R DATE"}
        }

        with m2:
            st.info("🔧 History (R Date)")
            for lbl, k in p_map.items(): st.write(f"**{lbl}:** {fmt(row.get(k['repl']))}")
        with m3:
            st.info("⏳ Remaining (Hrs)")
            for lbl, k in p_map.items():
                val = row.get(k['rem'], "N/A")
                icon = '🟢' if pd.notna(val) and str(val).replace('.','').replace('-','').isdigit() and float(val)>100 else '🔴'
                st.write(f"**{lbl}:** {icon} {val}")
        with m4:
            st.error("🚨 Next Due Date")
            for lbl, k in p_map.items(): st.write(f"**{lbl}:** {fmt(row.get(k['due']))}")

        st.divider()
        c1, c2 = st.columns(2)
        with c1: st.subheader("🎁 FOC"); st.dataframe(foc[foc[next(iter(foc.columns))].astype(str) == sel_f])
        with c2: st.subheader("🕒 History"); st.dataframe(service[service[next(iter(service.columns))].astype(str) == sel_f])

elif choice == "📦 Full FOC": st.dataframe(foc)
elif choice == "⏳ Overdue Service":
    over_col = next((c for c in master.columns if 'Overdue' in c or 'Red' in c), None)
    if over_col: st.dataframe(master[master[over_col] > 0])
elif choice == "📢 Automation Center":
    mail_link = f"mailto:crm@primepower.in?subject=Industrial Report&body=Check service pending list."
    st.markdown(f'<a href="{mail_link}"><button style="background-color:#0078D4; color:white; padding:12px; border-radius:5px; width:100%; cursor:pointer;">✉️ Prepare Email Draft</button></a>', unsafe_allow_html=True)
