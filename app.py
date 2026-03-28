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
    "user2": {"pass": "ind123", "role": "industrial"}
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
# 🏢 NAVIGATION & SIDEBAR
# ==============================
role = st.session_state["role"]
st.sidebar.title(f"👋 {st.session_state['user'].upper()}")
nav = st.sidebar.radio("Navigation:", ["DPSAC Tracker", "INDUSTRIAL Tracker", "📢 Automation Center"]) if role == "all" else (nav := "DPSAC Tracker" if role == "dpsac" else "INDUSTRIAL Tracker")

if st.sidebar.button("Logout"):
    st.session_state["login"] = False; st.rerun()

# ==============================
# 💎 TRACKER ENGINE
# ==============================
def run_tracker(df, name, key_suffix):
    st.title(f"🛠️ {name} Tracker Pro")
    
    cust_col = find_col(df, ["customer"])
    fab_col = find_col(df, ["fabrication"])

    t1, t2, t3 = st.tabs(["Machine Tracker", "📦 FOC List", "⏳ Service Pending"])
    
    with t1:
        colA, colB = st.columns(2)
        sel_c = colA.selectbox(f"Select Customer", ["All"] + sorted(df[cust_col].astype(str).unique()), key=f"sc_{key_suffix}")
        df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]
        sel_f = colB.selectbox(f"Select Fabrication Number", ["Select"] + sorted(df_f[fab_col].astype(str).unique()), key=f"sf_{key_suffix}")

        if sel_f != "Select":
            row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]
            
            # --- 📊 DYNAMIC INFO BOX ---
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.info("📋 Machine Info")
                if name == "DPSAC":
                    # Mapping Column AF, AG, DN, R
                    avg_run = row.get("Average Running Hours", "N/A") 
                    curr_h = row.get("Current Hours", 0)
                    total_h = row.get("Total Hours", 0)
                    diff_h = float(curr_h) - float(total_h) if (pd.notna(curr_h) and pd.notna(total_h)) else "N/A"
                    last_srv_date = row.get("Last Call Date", "N/A")
                    
                    st.write(f"**Cust:** {row[cust_col]}")
                    st.write(f"**Avg Running/Day:** {avg_run} 🏃")
                    st.write(f"**Current Hours (AG):** `{curr_h}` 📟")
                    st.write(f"**Total Hours (DN):** `{total_h}` 📊")
                    st.write(f"**Difference HMR:** `{diff_h}` ⚖️")
                    st.write(f"**Last Service Date (R):** {fmt(last_srv_date)} 📅")
                else:
                    # INDUSTRIAL LOOKUP
                    st.write(f"**Cust:** {row[cust_col]}")
                    st.write(f"**Current HMR:** `{row.get('CURRENT HMR', 'N/A')}`")
                    st.write(f"**MDA Total Hours:** `{row.get('MDA Total Hours', 'N/A')}`")
                    st.write(f"**Last Service Date:** {fmt(row.get('Last Call Date'))}")

                st.download_button("📄 Download Report", to_excel(pd.DataFrame([row])), f"Report_{sel_f}.xlsx", key=f"ex_{sel_f}")
            
            # --- 🔧 9 PARTS LOOKUP ---
            if name == "INDUSTRIAL":
                pm = {"OIL":["oil","r date"],"AF":["af","r date"],"OF":["of","r date"],"AOS":["aos","r date"],"RGT":["rgt","r date"],"VK":["vk","r date"],"PF":["pf","due"],"FF":["ff","due"],"CF":["cf","due"]}
            else:
                pm = {"OIL":["oil","repl"],"AFC":["afc","repl"],"AFE":["afe","repl"],"MOF":["mof","repl"],"ROF":["rof","repl"],"AOS":["aos","repl"],"RGT":["rgt","repl"],"1500":["1500","repl"],"3000":["3000","repl"]}

            with m2:
                st.info("🔧 History (R Date)")
                for lbl, ks in pm.items():
                    c = next((x for x in df.columns if all(k in x.lower() for k in ks)), None)
                    if not c: c = next((x for x in df.columns if lbl.lower() in x.lower() and "date" in x.lower() and "due" not in x.lower()), None)
                    st.write(f"**{lbl}:** {fmt(row.get(c))}")
            with m3:
                st.info("⏳ Remaining (HMR)")
                for lbl, ks in pm.items():
                    rc = next((x for x in df.columns if lbl.lower() in x.lower() and ("rem" in x.lower() or "remaining" in x.lower())), None)
                    val = row.get(rc, "N/A")
                    icon = '🟢' if pd.notna(val) and str(val).replace('.','').replace('-','').isdigit() and float(val)>100 else '🔴'
                    st.write(f"**{lbl}:** {icon} {val}")
            with m4:
                st.error("🚨 Next Due")
                for lbl, ks in pm.items():
                    dc = next((x for x in df.columns if lbl.lower() in x.lower() and "due" in x.lower() and "date" in x.lower()), None)
                    st.write(f"**{lbl}:** {fmt(row.get(dc))}")

            # --- 🎁 DEEP LINK: MACHINE FOC & HISTORY ---
            st.divider()
            c_foc, c_srv = st.columns(2)
            with c_foc:
                st.subheader(f"🎁 Machine FOC: {sel_f}")
                m_foc = foc_df[foc_df[find_col(foc_df, ["fabrication"])].astype(str) == sel_f] if not foc_df.empty else pd.DataFrame()
                if not m_foc.empty: st.dataframe(m_foc, use_container_width=True)
                else: st.warning("No FOC entries found.")
            with c_srv:
                st.subheader(f"🕒 Service History: {sel_f}")
                m_srv = service_df[service_df[find_col(service_df, ["fabrication"])].astype(str) == sel_f] if not service_df.empty else pd.DataFrame()
                if not m_srv.empty: st.dataframe(m_srv.sort_values(by=m_srv.columns[0], ascending=False), use_container_width=True)
                else: st.warning("No history recorded.")

# --- EXECUTION ---
if nav == "DPSAC Tracker": run_tracker(master_df, "DPSAC", "DP")
elif nav == "INDUSTRIAL Tracker": run_tracker(master_od_df, "INDUSTRIAL", "IN")
elif nav == "📢 Automation Center":
    st.title("📢 Automation Center")
    msg = st.text_area("Message:", "ELGi Service Update Required.")
    wa_link = f"https://wa.me/917061158953?text={urllib.parse.quote(msg)}"
    st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color:#25D366; color:white; padding:10px; border:none; border-radius:5px; width:100%; cursor:pointer;">Send WhatsApp Alert</button></a>', unsafe_allow_html=True)
