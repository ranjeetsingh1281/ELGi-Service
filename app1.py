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
    """Deep search for column values - ignores spaces and case"""
    target = str(target).strip().lower()
    for actual_col in row.index:
        clean_col = str(actual_col).strip().lower()
        if clean_col == target:
            return row[actual_col]
    return "N/A"

@st.cache_data
def load_data():
    try:
        m = pd.read_excel("Master_Data.xlsx", engine='openpyxl')
        f = pd.read_excel("Active_FOC.xlsx", engine='openpyxl')
        s = pd.read_excel("Service_Details.xlsx", engine='openpyxl')
        return m, f, s
    except Exception as e:
        st.error(f"File Load Error: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

master, foc, service = load_data()

# ==============================
# 🏢 NAVIGATION
# ==============================
st.sidebar.title(f"👋 {st.session_state['d_user'].upper()}")
nav_list = ["Machine Search", "📦 Full FOC List", "⏳ Overdue Service", "📢 Automation Center"]
if st.session_state["d_role"] == "viewer":
    nav_list.remove("📢 Automation Center")

choice = st.sidebar.radio("Navigation:", nav_list)

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()

# ==============================
# 💎 MACHINE SEARCH
# ==============================
if master.empty:
    st.error("🚨 Master_Data.xlsx nahi mili!")
    st.stop()

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
            h_val = get_col_val(row, "Current HMR") if get_col_val(row, "Current HMR") != "N/A" else get_col_val(row, "Current Hours")
            st.write(f"**Customer:** {row[cust_col]}")
            st.write(f"**HMR (Current):** `{h_val}`")
            st.write(f"**Last Call:** {fmt(get_col_val(row, 'Last Call Date'))}")

        # --- Exact Parts Logic for DPSAC ---
        # Note: 'rem' keys match your "OIL Rem", "AFC Rem" format
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

        # Machine level details
        st.divider()
        c_f, c_s = st.columns(2)
        with c_f:
            st.subheader("🎁 Machine FOC")
            f_fab = next((c for c in foc.columns if 'fabrication' in str(c).lower()), foc.columns[0])
            st.dataframe(foc[foc[f_fab].astype(str) == str(sel_f)], use_container_width=True)
        with c_s:
            st.subheader("🕒 Service History")
            s_fab = next((c for c in service.columns if 'fabrication' in str(c).lower()), service.columns[0])
            st.dataframe(service[service[s_fab].astype(str) == str(sel_f)], use_container_width=True)

# ==============================
# 📢 AUTOMATION CENTER (Fixed)
# ==============================
elif choice == "📢 Automation Center":
    st.title("📢 Automation Center")
    st.subheader("📱 WhatsApp Broadcast")
    msg = st.text_area("Message:", "ELGi Service Alert: Machine service is overdue.")
    wa_link = f"https://wa.me/917061158953?text={urllib.parse.quote(msg)}"
    st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color:#25D366; color:white; padding:12px; border-radius:5px; width:100%; cursor:pointer; font-weight:bold;">📱 Open WhatsApp</button></a>', unsafe_allow_html=True)
    
    st.divider()
    st.subheader("✉️ Email Draft")
    mail_link = "mailto:crm@primepower.in?subject=Service Alert&body=Check tracker for overdue machines."
    st.markdown(f'<a href="{mail_link}"><button style="background-color:#0078D4; color:white; padding:12px; border-radius:5px; width:100%; cursor:pointer; font-weight:bold;">✉️ Prepare Email Draft</button></a>', unsafe_allow_html=True)

# Other Tabs
elif choice == "📦 Full FOC List":
    st.dataframe(foc, use_container_width=True)
elif choice == "⏳ Overdue Service":
    over_c = next((c for c in master.columns if 'overdue' in str(c).lower()), master.columns[-1])
    st.dataframe(master[master[over_c] > 0], use_container_width=True)
