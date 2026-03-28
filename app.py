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
    if df.empty: return None
    for c in df.columns:
        if any(k.lower() in str(c).lower() for k in keywords): return c
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
elif role == "dpsac":
    nav = st.sidebar.radio("Navigation:", ["DPSAC Tracker", "📢 Automation Center"])
else:
    nav = st.sidebar.radio("Navigation:", ["INDUSTRIAL Tracker", "📢 Automation Center"])

if st.sidebar.button("Logout"):
    st.session_state["login"] = False; st.rerun()

# ==============================
# 💎 MAIN TRACKER ENGINE
# ==============================
def run_tracker(df, name, key_suffix):
    st.title(f"🛠️ {name} Tracker Pro")
    
    if df.empty:
        st.error(f"{name} Master file nahi mili!")
        return

    cust_col = find_col(df, ["customer"])
    fab_col = find_col(df, ["fabrication"])
    
    # 📊 Graphs
    with st.expander("📊 Click to View Dashboard Analytics", expanded=False):
        c1, c2 = st.columns(2)
        sc = find_col(df, ["unit", "status"])
        if sc: c1.bar_chart(df[sc].value_counts())
        cc = find_col(df, ["category"])
        if cc: c2.bar_chart(df[cc].value_counts())

    t1, t2, t3 = st.tabs(["Machine Search", "📦 Full FOC List", "⏳ Service Pending"])
    
    with t1:
        colA, colB = st.columns(2)
        sel_c = colA.selectbox("Select Customer", ["All"] + sorted(df[cust_col].astype(str).unique()), key=f"sc_{key_suffix}")
        df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]
        sel_f = colB.selectbox("Select Fabrication Number", ["Select"] + sorted(df_f[fab_col].astype(str).unique()), key=f"sf_{key_suffix}")

        if sel_f != "Select":
            row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]
            
            # --- Quick Display ---
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.info("📋 Info")
                curr_h = row.get("Current Hours", row.get("CURRENT HMR", row.get("Current HMR", 0)))
                st.write(f"**Customer:** {row[cust_col]}")
                st.write(f"**HMR:** `{curr_h}`")
                st.download_button("📄 Export Row", to_excel(pd.DataFrame([row])), f"Report_{sel_f}.xlsx", key=f"dl_{sel_f}")
            
            # --- Parts Lookup (Simplified Search) ---
            parts = ["OIL", "AF", "OF", "AOS", "RGT", "VK"]
            with m2:
                st.info("🔧 History")
                for p in parts:
                    c = find_col(df, [p, "date"]) or find_col(df, [p, "repl"])
                    if c: st.write(f"**{p}:** {fmt(row.get(c))}")
            with m3:
                st.info("⏳ Remaining")
                for p in parts:
                    c = find_col(df, [p, "rem"])
                    if c: st.write(f"**{p}:** {row.get(c, 'N/A')}")
            with m4:
                st.error("🚨 Next Due")
                for p in parts:
                    c = find_col(df, [p, "due"])
                    if c: st.write(f"**{p}:** {fmt(row.get(c))}")

            # --- MACHINE LEVEL FOC & SERVICE HISTORY (Fixed) ---
            st.divider()
            c_foc, c_srv = st.columns(2)
            with c_foc:
                st.subheader(f"🎁 Machine FOC: {sel_f}")
                f_fab = find_col(foc_df, ["fabrication"])
                if f_fab:
                    m_foc = foc_df[foc_df[f_fab].astype(str).str.strip() == str(sel_f).strip()]
                    st.dataframe(m_foc, use_container_width=True)
                else: st.warning("FOC Column missing")
            
            with c_srv:
                st.subheader(f"🕒 Service History: {sel_f}")
                s_fab = find_col(service_df, ["fabrication"])
                if s_fab:
                    # Fabrication matches accurately
                    m_srv = service_df[service_df[s_fab].astype(str).str.strip() == str(sel_f).strip()]
                    if not m_srv.empty:
                        st.dataframe(m_srv.sort_values(by=m_srv.columns[0], ascending=False), use_container_width=True)
                    else: st.warning("History entries nahi mili.")
                else: st.error("Service Details mein Fabrication column nahi mila.")

    with t2:
        f_fab = find_col(foc_df, ["fabrication"])
        if f_fab: st.dataframe(foc_df[foc_df[f_fab].astype(str).isin(df[fab_col].astype(str))], use_container_width=True)

    with t3:
        over_col = find_col(df, ["over", "due"])
        if over_col: st.dataframe(df[df[over_col] > 0], use_container_width=True)

# ==============================
# 📢 AUTOMATION CENTER
# ==============================
if nav == "📢 Automation Center":
    st.title("📢 Automation Center")
    col1, col2 = st.columns(2)
    with col1:
        msg = st.text_area("WA Message:", "ELGi Alert: Machine service is overdue.")
        wa_link = f"https://wa.me/917061158953?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color:#25D366; color:white; padding:12px; border-radius:5px; width:100%; cursor:pointer;">📱 Open WhatsApp</button></a>', unsafe_allow_html=True)
    with col2:
        mail_link = f"mailto:crm@primepower.in?subject=Service Report&body=Please find the report attached."
        st.markdown(f'<a href="{mail_link}"><button style="background-color:#0078D4; color:white; padding:12px; border-radius:5px; width:100%; cursor:pointer;">✉️ Prepare Email Draft</button></a>', unsafe_allow_html=True)

# --- EXECUTION ---
if nav == "DPSAC Tracker": run_tracker(master_df, "DPSAC", "DP")
elif nav == "INDUSTRIAL Tracker": run_tracker(master_od_df, "INDUSTRIAL", "IN")
