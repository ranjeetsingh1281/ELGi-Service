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

def find_col(df, keywords):
    for c in df.columns:
        if all(k.lower() in str(c).lower() for k in keywords): return c
    return None

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
elif role == "dpsac": nav = "DPSAC Tracker"
else: nav = "INDUSTRIAL Tracker"

if st.sidebar.button("Logout"):
    st.session_state["login"] = False; st.rerun()

# ==============================
# 💎 MAIN TRACKER ENGINE
# ==============================
def run_tracker(df, name, key_suffix):
    st.title(f"🛠️ {name} Tracker Pro")
    
    cust_col = find_col(df, ["customer"])
    fab_col = find_col(df, ["fabrication"])
    overdue_col = find_col(df, ["over", "due"]) or find_col(df, ["red", "count"])
    crit = df[df[overdue_col] > 0] if overdue_col in df.columns else pd.DataFrame()

    # 📊 GRAPHS SECTION (Wapas Joda Gaya)
    with st.expander("📊 Click to View Dashboard Analytics & Graphs", expanded=False):
        c1, c2 = st.columns(2)
        sc = find_col(df, ["unit", "status"])
        if sc: 
            c1.subheader("Unit Status Distribution")
            c1.bar_chart(df[sc].value_counts())
        cc = find_col(df, ["category"])
        if cc: 
            c2.subheader("Category Breakdown")
            c2.bar_chart(df[cc].value_counts())

    t1, t2, t3 = st.tabs(["Machine Search", "📦 Full FOC List", "⏳ Service Pending"])
    
    with t1:
        colA, colB = st.columns(2)
        sel_c = colA.selectbox(f"Select Customer", ["All"] + sorted(df[cust_col].astype(str).unique()), key=f"sc_{key_suffix}")
        df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]
        sel_f = colB.selectbox(f"Select Fabrication Number", ["Select"] + sorted(df_f[fab_col].astype(str).unique()), key=f"sf_{key_suffix}")

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
            
            # --- Parts Mapping ---
            if name == "INDUSTRIAL":
                parts_map = {
                    "OIL": {"repl": ["MDA Oil R Date"], "rem": ["OIL Rem"], "due": ["Oil R Date"]},
                    "AF": {"repl": ["MDA AF R Date"], "rem": ["AF Rem"], "due": ["AF R Date"]},
                    "OF": {"repl": ["MDA OF R Date"], "rem": ["OF Rem"], "due": ["OF R Date"]},
                    "AOS": {"repl": ["MDA AOS R Date"], "rem": ["AOS Rem"], "due": ["AOS R Date"]},
                    "RGT": {"repl": ["MDA RGT R Date"], "rem": ["RGT Rem"], "due": ["RGT R Date"]},
                    "VK": {"repl": ["MDA Valvekit R Date"], "rem": ["VK Rem"], "due": ["Valvekit R Date"]},
                    "PF": {"repl": ["MDA PF R DATE"], "rem": ["PF Rem"], "due": ["PF R DATE"]},
                    "FF": {"repl": ["MDA FF R DATE"], "rem": ["FF Rem"], "due": ["FF R DATE"]},
                    "CF": {"repl": ["MDA CF R DATE"], "rem": ["CF Rem"], "due": ["CF R DATE"]}
                }
            else:
                parts_map = {
                    "OIL": {"repl": ["oil r date"], "rem": ["oil rem"], "due": ["oil due"]},
                    "AFC": {"repl": ["afc r date"], "rem": ["afc rem"], "due": ["afc due"]},
                    "AFE": {"repl": ["afe r date"], "rem": ["afe rem"], "due": ["afe due"]},
                    "MOF": {"repl": ["mof r date"], "rem": ["mof rem"], "due": ["mof due"]},
                    "ROF": {"repl": ["rof r date"], "rem": ["rof rem"], "due": ["rof due"]},
                    "AOS": {"repl": ["aos r date"], "rem": ["aos rem"], "due": ["aos due"]},
                    "RGT": {"repl": ["rgt r date"], "rem": ["rgt rem"], "due": ["rgt due"]},
                    "1500": {"repl": ["1500 r date"], "rem": ["1500 rem"], "due": ["1500 due"]},
                    "3000": {"repl": ["3000 r date"], "rem": ["3000 rem"], "due": ["3000 due"]}
                }

            with m2:
                st.info("🔧 History (R Date)")
                for lbl, ks in parts_map.items():
                    c = next((x for x in df.columns if any(k.lower() in x.lower() for k in ks["repl"])), None)
                    st.write(f"**{lbl}:** {fmt(row.get(c))}")
            with m3:
                st.info("⏳ Remaining (Hrs)")
                for lbl, ks in parts_map.items():
                    c = next((x for x in df.columns if any(k.lower() in x.lower() for k in ks["rem"])), None)
                    val = row.get(c, "N/A")
                    icon = '🟢' if pd.notna(val) and str(val).replace('.','').replace('-','').isdigit() and float(val)>100 else '🔴'
                    st.write(f"**{lbl}:** {icon} {val}")
            with m4:
                st.error("🚨 Next Due Date")
                for lbl, ks in parts_map.items():
                    c = next((x for x in df.columns if any(k.lower() in x.lower() for k in ks["due"])), None)
                    st.write(f"**{lbl}:** {fmt(row.get(c))}")

            # --- MACHINE LEVEL FOC & HISTORY (Wapas Joda Gaya) ---
            st.divider()
            c_foc, c_srv = st.columns(2)
            with c_foc:
                st.subheader(f"🎁 Machine FOC: {sel_f}")
                foc_fab_col = find_col(foc_df, ["fabrication"])
                if foc_fab_col:
                    m_foc = foc_df[foc_df[foc_fab_col].astype(str) == sel_f]
                    st.dataframe(m_foc, use_container_width=True) if not m_foc.empty else st.warning("No FOC entries")
            with c_srv:
                st.subheader(f"🕒 Service History: {sel_f}")
                srv_fab_col = find_col(service_df, ["fabrication"])
                if srv_fab_col:
                    m_srv = service_df[service_df[srv_fab_col].astype(str) == sel_f]
                    st.dataframe(m_srv.sort_values(by=m_srv.columns[0], ascending=False), use_container_width=True) if not m_srv.empty else st.warning("No History")

    with t2:
        st.subheader(f"📦 {name} Full FOC List")
        f_fab_col = find_col(foc_df, ["fabrication"])
        if f_fab_col:
            f_display = foc_df[foc_df[f_fab_col].astype(str).isin(df[fab_col].astype(str))]
            st.dataframe(f_display, use_container_width=True)
            st.download_button("📥 Download FOC", to_excel(f_display), f"{name}_FOC.xlsx", key=f"foc_all_{key_suffix}")

    with t3:
        st.subheader(f"⏳ {name} Service Pending")
        if not crit.empty:
            st.dataframe(crit, use_container_width=True)
            st.download_button("📥 Download Pending", to_excel(crit), f"{name}_Pending.xlsx", key=f"crit_all_{key_suffix}")
        else: st.success("Everything up to date!")

# ==============================
# 📢 AUTOMATION CENTER
# ==============================
if nav == "📢 Automation Center":
    st.title("📢 Automation Center")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📱 WhatsApp Broadcast")
        msg = st.text_area("WA Message:", "ELGi Service Alert: Machine is overdue.")
        wa_link = f"https://wa.me/917061158953?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color:#25D366; color:white; padding:12px; border:none; border-radius:5px; width:100%; cursor:pointer; font-weight:bold;">📱 Open WhatsApp</button></a>', unsafe_allow_html=True)
    with col2:
        st.subheader("✉️ Email Notification")
        mail_link = f"mailto:crm@primepower.in?subject=Service Report&body=Please find the attached service report."
        st.markdown(f'<a href="{mail_link}"><button style="background-color:#0078D4; color:white; padding:12px; border:none; border-radius:5px; width:100%; cursor:pointer; font-weight:bold;">✉️ Prepare Email Draft</button></a>', unsafe_allow_html=True)

# --- EXECUTION ---
if nav == "DPSAC Tracker": run_tracker(master_df, "DPSAC", "DP")
elif nav == "INDUSTRIAL Tracker": run_tracker(master_od_df, "INDUSTRIAL", "IN")
