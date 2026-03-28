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
    "user2": {"pass": "ind123", "role": "industrial"},
    "user3": {"pass": "view456", "role": "viewer"}
}

def login():
    st.title("🔐 ELGi Global Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USER_DB and USER_DB[u]["pass"] == p:
            st.session_state["login"], st.session_state["user"], st.session_state["role"] = True, u, USER_DB[u]["role"]
            st.rerun()
        else: st.error("Invalid Credentials")

if "login" not in st.session_state or not st.session_state["login"]:
    login(); st.stop()

# ==============================
# ⚙️ CONFIG & HELPERS
# ==============================
st.set_page_config(page_title="ELGi Global Tracker Pro", layout="wide")

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
def load_all_data():
    f_list = os.listdir('.')
    def f(name): return next((x for x in f_list if name.lower() in x.lower() and x.endswith('.xlsx')), None)
    try:
        m_df = pd.read_excel(f("Master_Data"), engine='openpyxl') if f("Master_Data") else pd.DataFrame()
        m_od_df = pd.read_excel(f("Master_OD_Data"), engine='openpyxl') if f("Master_OD_Data") else pd.DataFrame()
        foc_df = pd.read_excel(f("Active_FOC"), engine='openpyxl') if f("Active_FOC") else pd.DataFrame()
        srv_df = pd.read_excel(f("Service_Details"), engine='openpyxl') if f("Service_Details") else pd.DataFrame()
        for d in [m_df, m_od_df, foc_df, srv_df]:
            if not d.empty: d.columns = [str(c).strip() for c in d.columns]
        return m_df, m_od_df, foc_df, srv_df
    except Exception: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

master_df, master_od_df, foc_df, service_df = load_all_data()

# ==============================
# 🏢 NAVIGATION
# ==============================
role = st.session_state["role"]
st.sidebar.title(f"👋 {st.session_state['user'].upper()}")

if role == "all":
    nav = st.sidebar.radio("Navigation:", ["DPSAC Tracker", "INDUSTRIAL Tracker", "📢 Automation Center"])
elif role == "viewer":
    nav = st.sidebar.radio("Navigation:", ["DPSAC Tracker", "INDUSTRIAL Tracker"])
else:
    nav = st.sidebar.radio(("DPSAC Tracker" if role == "dpsac" else "INDUSTRIAL Tracker"), ["📢 Automation Center"])

if st.sidebar.button("Logout"):
    st.session_state["login"] = False; st.rerun()

# ==============================
# 💎 MAIN TRACKER ENGINE
# ==============================
def run_tracker(df, name, key_suffix):
    st.title(f"🛠️ {name} Tracker Pro")
    
    # Static Column Detection
    cust_col = next((c for c in df.columns if 'Customer' in c), df.columns[0])
    fab_col = next((c for c in df.columns if 'Fabrication' in c), df.columns[1])
    
    t1, t2, t3 = st.tabs(["Machine Search", "📦 Full FOC List", "⏳ Service Pending"])
    
    with t1:
        colA, colB = st.columns(2)
        sel_c = colA.selectbox("Select Customer", ["All"] + sorted(df[cust_col].astype(str).unique()), key=f"sc_{key_suffix}")
        df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]
        sel_f = colB.selectbox("Select Fabrication Number", ["Select"] + sorted(df_f[fab_col].astype(str).unique()), key=f"sf_{key_suffix}")

        if sel_f != "Select":
            row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]
            
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.info("📋 Basic Info")
                curr_h = row.get("Current Hours", row.get("CURRENT HMR", row.get("Current HMR", 0)))
                st.write(f"**Customer:** {row[cust_col]}")
                st.write(f"**HMR (Current):** `{curr_h}`")
                st.write(f"**Last Call:** {fmt(row.get('Last Call Date'))}")
                st.download_button("📄 Export Row", to_excel(pd.DataFrame([row])), f"Report_{sel_f}.xlsx", key=f"dl_{sel_f}")
            
            # --- 🛠️ EXACT PARTS MAPPING (Jaisa Excel mein hai) ---
            if name == "INDUSTRIAL":
                # INDUSTRIAL Exact Headings
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
            else:
                # DPSAC Exact Headings (Purana Logic)
                p_map = {
                    "OIL": {"repl": "oil r date", "rem": "oil rem", "due": "oil due"},
                    "AFC": {"repl": "afc r date", "rem": "afc rem", "due": "afc due"},
                    "AFE": {"repl": "afe r date", "rem": "afe rem", "due": "afe due"},
                    "MOF": {"repl": "mof r date", "rem": "mof rem", "due": "mof due"},
                    "ROF": {"repl": "rof r date", "rem": "rof rem", "due": "rof due"},
                    "AOS": {"repl": "aos r date", "rem": "aos rem", "due": ["aos due", "AOS Due Date"]},
                    "RGT": {"repl": "rgt r date", "rem": "rgt rem", "due": "rgt due"},
                    "1500": {"repl": "1500 r date", "rem": "1500 rem", "due": "1500 due"},
                    "3000": {"repl": "3000 r date", "rem": "3000 rem", "due": "3000 due"}
                }

            with m2:
                st.info("🔧 History (R Date)")
                for lbl, k in p_map.items():
                    st.write(f"**{lbl}:** {fmt(row.get(k['repl']))}")
            with m3:
                st.info("⏳ Remaining (Hrs)")
                for lbl, k in p_map.items():
                    val = row.get(k['rem'], "N/A")
                    icon = '🟢' if pd.notna(val) and str(val).replace('.','').replace('-','').isdigit() and float(val)>100 else '🔴'
                    st.write(f"**{lbl}:** {icon} {val}")
            with m4:
                st.error("🚨 Next Due Date")
                for lbl, k in p_map.items():
                    # Handle multiple possible due date names for DPSAC if needed
                    due_val = row.get(k['due']) if isinstance(k['due'], str) else next((row.get(x) for x in k['due'] if x in row), None)
                    st.write(f"**{lbl}:** {fmt(due_val)}")

            # --- MACHINE LEVEL FOC & HISTORY ---
            st.divider()
            c_foc, c_srv = st.columns(2)
            with c_foc:
                st.subheader(f"🎁 Machine FOC: {sel_f}")
                if not foc_df.empty:
                    f_col = next((c for c in foc_df.columns if 'Fabrication' in c), foc_df.columns[0])
                    m_foc = foc_df[foc_df[f_col].astype(str).str.strip() == str(sel_f).strip()]
                    st.dataframe(m_foc, use_container_width=True)
            with c_srv:
                st.subheader(f"🕒 Service History: {sel_f}")
                if not service_df.empty:
                    s_col = next((c for c in service_df.columns if 'Fabrication' in c), service_df.columns[0])
                    m_srv = service_df[service_df[s_col].astype(str).str.strip() == str(sel_f).strip()]
                    st.dataframe(m_srv.sort_values(by=m_srv.columns[0], ascending=False), use_container_width=True)

    with t2:
        st.subheader(f"📦 {name} Full FOC List")
        f_col = next((c for c in foc_df.columns if 'Fabrication' in c), None)
        if f_col:
            f_display = foc_df[foc_df[f_col].astype(str).isin(df[fab_col].astype(str))]
            st.dataframe(f_display, use_container_width=True)

    with t3:
        st.subheader(f"⏳ {name} Service Pending")
        over_col = next((c for c in df.columns if 'Overdue' in c or 'Red' in c), None)
        if over_col:
            st.dataframe(df[df[over_col] > 0], use_container_width=True)

# ==============================
# 📢 AUTOMATION CENTER
# ==============================
if nav == "📢 Automation Center":
    st.title("📢 Automation Center")
    col1, col2 = st.columns(2)
    with col1:
        msg = st.text_area("WA Message:", "ELGi Service Alert: Machine service is overdue.")
        wa_link = f"https://wa.me/917061158953?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color:#25D366; color:white; padding:12px; border-radius:5px; width:100%; cursor:pointer; font-weight:bold;">📱 Open WhatsApp</button></a>', unsafe_allow_html=True)
    with col2:
        mail_link = f"mailto:crm@primepower.in?subject=Service Report&body=Attached service report draft."
        st.markdown(f'<a href="{mail_link}"><button style="background-color:#0078D4; color:white; padding:12px; border-radius:5px; width:100%; cursor:pointer; font-weight:bold;">✉️ Prepare Email Draft</button></a>', unsafe_allow_html=True)

# --- EXECUTION ---
if nav == "DPSAC Tracker": run_tracker(master_df, "DPSAC", "DP")
elif nav == "INDUSTRIAL Tracker": run_tracker(master_od_df, "INDUSTRIAL", "IN")
