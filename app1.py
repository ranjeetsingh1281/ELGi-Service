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

def smart_get(row, keywords):
    """Keywords ke basis par column dhoondne ka sabse powerful tarika"""
    for col in row.index:
        col_clean = str(col).strip().lower()
        if all(k.lower() in col_clean for k in keywords):
            return row[col]
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
if choice == "Machine Search":
    if master.empty:
        st.error("🚨 Master_Data.xlsx load nahi ho saki!")
        st.stop()

    cust_col = next((c for c in master.columns if 'customer' in str(c).lower()), master.columns[0])
    fab_col = next((c for c in master.columns if 'fabrication' in str(c).lower()), master.columns[1])

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
            hmr = smart_get(row, ["current", "hmr"])
            if hmr == "N/A": hmr = smart_get(row, ["current", "hours"])
            st.write(f"**Customer:** {row[cust_col]}")
            st.write(f"**HMR (Current):** `{hmr}`")
            st.write(f"**Last Call:** {fmt(smart_get(row, ['last', 'call']))}")

        # --- SMART PARTS LOOKUP ---
        parts = ["OIL", "AFC", "AFE", "MOF", "ROF", "AOS", "RGT", "1500", "3000"]
        
        with m2:
            st.info("🔧 History (R Date)")
            for p in parts:
                st.write(f"**{p}:** {fmt(smart_get(row, [p, 'date']))}")
        
        with m3:
            st.info("⏳ Remaining (Hrs)")
            for p in parts:
                val = smart_get(row, [p, 'rem'])
                icon = '🟢' if pd.notna(val) and str(val).replace('.','').replace('-','').isdigit() and float(val)>100 else '🔴'
                st.write(f"**{p}:** {icon} {val}")
        
        with m4:
            st.error("🚨 Next Due Date")
            for p in parts:
                st.write(f"**{p}:** {fmt(smart_get(row, [p, 'due']))}")

        # Machine level FOC & History
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
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📱 WhatsApp Broadcast")
        msg = st.text_area("Message:", "ELGi Service Alert: Machine service is overdue.")
        wa_link = f"https://wa.me/917061158953?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color:#25D366; color:white; padding:12px; border-radius:5px; width:100%; cursor:pointer; font-weight:bold;">📱 Open WhatsApp</button></a>', unsafe_allow_html=True)
    with c2:
        st.subheader("✉️ Email Draft")
        mail_link = "mailto:crm@primepower.in?subject=Service Alert&body=Check tracker for overdue machines."
        st.markdown(f'<a href="{mail_link}"><button style="background-color:#0078D4; color:white; padding:12px; border-radius:5px; width:100%; cursor:pointer; font-weight:bold;">✉️ Prepare Email Draft</button></a>', unsafe_allow_html=True)

# Full Tables
elif choice == "📦 Full FOC List":
    st.dataframe(foc, use_container_width=True)
elif choice == "⏳ Overdue Service":
    st.title("⏳ Service Pending (Red List)")
    
    # Overdue column dhoondna
    over_c = next((c for c in master.columns if 'overdue' in str(c).lower()), None)
    
    if over_c:
        # Error Fix: Column ko numeric mein convert karna (errors='coerce' se text '0' ban jayega)
        master[over_c] = pd.to_numeric(master[over_c], errors='coerce').fillna(0)
        
        # Ab filter karna safe hai
        overdue_df = master[master[over_c] > 0]
        
        if not overdue_df.empty:
            st.success(f"Total {len(overdue_df)} machines overdue mili hain.")
            st.dataframe(overdue_df, use_container_width=True)
            st.download_button("📥 Download Red List", to_excel(overdue_df), "Overdue_Report.xlsx")
        else:
            st.success("✅ Sab sahi hai! Koi bhi machine overdue nahi hai.")
    else:
        st.error("🚨 Excel mein 'Overdue' naam ka column nahi mila. Column name check karein.")
