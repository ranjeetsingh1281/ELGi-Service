import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime
from io import BytesIO

# ==============================
# 🔐 LOGIN SYSTEM (INDUSTRIAL)
# ==============================
USER_DB = {
    "admin": {"pass": "admin123", "role": "all"},
    "user2": {"pass": "ind123", "role": "industrial"},
    "user3": {"pass": "view456", "role": "viewer"}
}

if "i_login" not in st.session_state:
    st.title("🏗️ ELGi INDUSTRIAL Tracker Login")
    u = st.text_input("Username", key="ind_u")
    p = st.text_input("Password", type="password", key="ind_p")
    if st.button("Login"):
        if u in USER_DB and USER_DB[u]["pass"] == p:
            st.session_state["i_login"], st.session_state["i_role"], st.session_state["i_user"] = True, USER_DB[u]["role"], u
            st.rerun()
        else: st.error("Invalid Credentials")
    st.stop()

# ==============================
# ⚙️ HELPERS
# ==============================
st.set_page_config(page_title="ELGi Industrial Tracker Pro", layout="wide")

def fmt(dt):
    if pd.isna(dt) or dt == 0 or str(dt).lower() in ["nan", "nat"]: return "N/A"
    try:
        val = pd.to_datetime(dt)
        return val.strftime('%d-%b-%y') if val.year > 1970 else "N/A"
    except: return "N/A"

def smart_get(row, keywords):
    """Industrial MDA columns dhoondne ke liye advanced logic"""
    for col in row.index:
        col_clean = str(col).strip().lower()
        if all(k.lower() in col_clean for k in keywords):
            return row[col]
    return "N/A"

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# ==============================
# 📂 DATA LOADING
# ==============================
@st.cache_data
def load_ind_data():
    try:
        # INDUSTRIAL specific master file
        m = pd.read_excel("Master_OD_Data.xlsx", engine='openpyxl')
        f = pd.read_excel("Active_FOC.xlsx", engine='openpyxl')
        s = pd.read_excel("Service_Details.xlsx", engine='openpyxl')
        for d in [m, f, s]:
            if not d.empty: d.columns = [str(c).strip() for c in d.columns]
        return m, f, s
    except Exception as e:
        st.error(f"Files missing: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

master_od, foc, service = load_ind_data()

# ==============================
# 🏢 NAVIGATION
# ==============================
st.sidebar.title(f"👋 {st.session_state['i_user'].upper()}")
nav_list = ["Machine Search", "📦 Full FOC List", "⏳ Overdue Service", "📢 Automation Center"]
if st.session_state["i_role"] == "viewer": nav_list.remove("📢 Automation Center")
choice = st.sidebar.radio("Navigation:", nav_list)

if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()

# ==============================
# 💎 INDUSTRIAL ENGINE
# ==============================
if master_od.empty:
    st.error("🚨 'Master_OD_Data.xlsx' nahi mili!")
    st.stop()

# Detect Base Columns
cust_col = next((c for c in master_od.columns if 'customer' in str(c).lower()), master_od.columns[0])
fab_col = next((c for c in master_od.columns if 'fabrication' in str(c).lower()), master_od.columns[1])

if choice == "Machine Search":
    st.title("🛠️ Industrial Machine Tracker")
    c1, c2 = st.columns(2)
    sel_c = c1.selectbox("Select Customer", ["All"] + sorted(master_od[cust_col].astype(str).unique()))
    df_f = master_od if sel_c == "All" else master_od[master_od[cust_col] == sel_c]
    sel_f = c2.selectbox("Select Fabrication Number", ["Select"] + sorted(df_f[fab_col].astype(str).unique()))

    if sel_f != "Select":
        row = df_f[df_f[fab_col].astype(str) == str(sel_f)].iloc[0]
        m1, m2, m3, m4 = st.columns(4)
        
        with m1:
            st.info("📋 Basic Info")
            hmr = smart_get(row, ["current", "hmr"])
            st.write(f"**Customer:** {row[cust_col]}")
            st.write(f"**HMR (Current):** `{hmr}`")
            st.write(f"**Last Call:** {fmt(smart_get(row, ['last', 'call']))}")

        # INDUSTRIAL MDA Mapping
        parts = {
            "OIL": {"repl": "MDA Oil R Date", "rem": "OIL Rem", "due": "Oil R Date"},
            "AF": {"repl": "MDA AF R Date", "rem": "AF Rem", "due": "AF R Date"},
            "OF": {"repl": "MDA OF R Date", "rem": "OF Rem", "due": "OF R Date"},
            "AOS": {"repl": "MDA AOS R Date", "rem": "AOS Rem", "due": "AOS R Date"},
            "RGT": {"repl": "MDA RGT R Date", "rem": "RGT Rem", "due": "RGT R Date"},
            "VK": {"repl": "MDA Valvekit R Date", "rem": "VK Rem", "due": "Valvekit R Date"}
        }

        with m2:
            st.info("🔧 History (R Date)")
            for lbl, k in parts.items(): st.write(f"**{lbl}:** {fmt(smart_get(row, [k['repl']]))}")
        with m3:
            st.info("⏳ Remaining (Hrs)")
            for lbl, k in parts.items():
                val = smart_get(row, [k['rem']])
                icon = '🟢' if pd.notna(val) and str(val).replace('.','').replace('-','').isdigit() and float(val)>100 else '🔴'
                st.write(f"**{lbl}:** {icon} {val}")
        with m4:
            st.error("🚨 Next Due Date")
            for lbl, k in parts.items(): st.write(f"**{lbl}:** {fmt(smart_get(row, [k['due']]))}")

        # --- FIX 1: FOC & HISTORY APPEARED ---
        st.divider()
        low1, low2 = st.columns(2)
        with low1:
            st.subheader("🎁 Machine FOC List")
            f_fab = next((c for c in foc.columns if 'fabrication' in str(c).lower()), foc.columns[0])
            st.dataframe(foc[foc[f_fab].astype(str) == str(sel_f)], use_container_width=True)
        with low2:
            st.subheader("🕒 Service History")
            s_fab = next((c for c in service.columns if 'fabrication' in str(c).lower()), service.columns[0])
            st.dataframe(service[service[s_fab].astype(str) == str(sel_f)], use_container_width=True)

# --- FIX 2: OVERDUE SERVICE LIST ---
elif choice == "⏳ Overdue Service":
    st.title("⏳ Overdue Service List (Industrial)")
    over_c = next((c for c in master_od.columns if any(k in str(c).lower() for k in ['overdue', 'red', 'pending'])), None)
    if over_c:
        master_od[over_c] = pd.to_numeric(master_od[over_c], errors='coerce').fillna(0)
        overdue_df = master_od[master_od[over_c] > 0]
        if not overdue_df.empty:
            st.warning(f"Total {len(overdue_df)} Industrial machines overdue.")
            st.dataframe(overdue_df, use_container_width=True)
            st.download_button("📥 Export Red List", to_excel(overdue_df), "Ind_Overdue.xlsx")
        else: st.success("✅ No overdue machines found.")
    else: st.error("Excel mein 'Overdue' column nahi mila.")

# --- FIX 3: AUTOMATION CENTRE WHATSAPP ---
elif choice == "📢 Automation Center":
    st.title("📢 Automation Center")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📱 WhatsApp Alert")
        msg = st.text_area("Message:", "ELGi Industrial Service Alert: Your machine is overdue.")
        wa_link = f"https://wa.me/917061158953?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color:#25D366; color:white; padding:12px; border:none; border-radius:5px; width:100%; cursor:pointer; font-weight:bold;">📱 Open WhatsApp</button></a>', unsafe_allow_html=True)
    with c2:
        st.subheader("✉️ Email Draft")
        mail_link = "mailto:crm@primepower.in?subject=Industrial Service Report&body=Check overdue machines."
        st.markdown(f'<a href="{mail_link}"><button style="background-color:#0078D4; color:white; padding:12px; border-radius:5px; width:100%; cursor:pointer; font-weight:bold;">✉️ Prepare Email Draft</button></a>', unsafe_allow_html=True)

elif choice == "📦 Full FOC List":
    st.dataframe(foc, use_container_width=True)
