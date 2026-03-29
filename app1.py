import streamlit as st
import pandas as pd
import os
import urllib.parse
from io import BytesIO

# ==============================
# 🔐 LOGIN SYSTEM (DPSAC)
# ==============================
USER_DB = {
    "admin": {"pass": "admin123", "role": "all"},
    "user1": {"pass": "dpsac123", "role": "dpsac"},
    "user3": {"pass": "view456", "role": "viewer"}
}

def login():
    st.title("🚜 ELGi DPSAC Tracker Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USER_DB and USER_DB[u]["pass"] == p:
            st.session_state["d_login"], st.session_state["d_role"], st.session_state["d_user"] = True, USER_DB[u]["role"], u
            st.rerun()
        else: st.error("Invalid Credentials")

if "d_login" not in st.session_state:
    login(); st.stop()

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

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

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
# 💎 MAIN ENGINE
# ==============================
st.title("🛠️ DPSAC Service Tracker Pro")
role = st.session_state["d_role"]

# Sidebar
if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()

nav = ["Machine Search", "📦 Full FOC", "⏳ Overdue Service"]
if role != "viewer": nav.append("📢 Automation Center")
choice = st.sidebar.radio("Navigation:", nav)

if choice == "Machine Search":
    cust_col = next((c for c in master.columns if 'Customer' in c), master.columns[0])
    fab_col = next((c for c in master.columns if 'Fabrication' in c), master.columns[1])
    
    colA, colB = st.columns(2)
    sel_c = colA.selectbox("Select Customer", ["All"] + sorted(master[cust_col].astype(str).unique()))
    df_f = master if sel_c == "All" else master[master[cust_col] == sel_c]
    sel_f = colB.selectbox("Select Fabrication Number", ["Select"] + sorted(df_f[fab_col].astype(str).unique()))

    if sel_f != "Select":
        row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            st.info("📋 Basic Info")
            st.write(f"**Customer:** {row[cust_col]}")
            st.write(f"**Current HMR:** `{row.get('Current Hours', row.get('Current HMR', 0))}`")
            st.write(f"**Last Call:** {fmt(row.get('Last Call Date'))}")
            st.download_button("📄 Export Row", to_excel(pd.DataFrame([row])), f"DPSAC_{sel_f}.xlsx")

        p_map = {
            "OIL": {"repl": "oil r date", "rem": "oil rem", "due": "oil due"},
            "AFC": {"repl": "afc r date", "rem": "afc rem", "due": "afc due"},
            "AFE": {"repl": "afe r date", "rem": "afe rem", "due": "afe due"},
            "MOF": {"repl": "mof r date", "rem": "mof rem", "due": "mof due"},
            "ROF": {"repl": "rof r date", "rem": "rof rem", "due": "rof due"},
            "AOS": {"repl": "aos r date", "rem": "aos rem", "due": "aos due"},
            "RGT": {"repl": "rgt r date", "rem": "rgt rem", "due": "rgt due"},
            "1500": {"repl": "1500 r date", "rem": "1500 rem", "due": "1500 due"},
            "3000": {"repl": "3000 r date", "rem": "3000 rem", "due": "3000 due"}
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
        with c1: st.subheader("🎁 Machine FOC"); st.dataframe(foc[foc[next(iter(foc.columns))].astype(str) == sel_f])
        with c2: st.subheader("🕒 Service History"); st.dataframe(service[service[next(iter(service.columns))].astype(str) == sel_f])

elif choice == "📦 Full FOC": st.dataframe(foc)
elif choice == "⏳ Overdue Service":
    over_col = next((c for c in master.columns if 'Overdue' in c or 'Red' in c), None)
    if over_col: st.dataframe(master[master[over_col] > 0])
elif choice == "📢 Automation Center":
    msg = st.text_area("WA Message:", "ELGi DPSAC Alert!")
    wa_link = f"https://wa.me/917061158953?text={urllib.parse.quote(msg)}"
    st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color:#25D366; color:white; padding:12px; border-radius:5px; width:100%; cursor:pointer;">📱 WhatsApp</button></a>', unsafe_allow_html=True)
