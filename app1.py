import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime
from io import BytesIO

# ==============================
# 🔐 LOGIN
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
            st.session_state["d_login"] = True
            st.session_state["d_user"] = u
            st.session_state["d_role"] = USER_DB[u]["role"]
            st.rerun()
        else:
            st.error("Invalid Credentials")

    st.stop()

# ==============================
# ⚙️ CONFIG
# ==============================
st.set_page_config(layout="wide")

# ==============================
# 🧠 HELPERS
# ==============================
def fmt(dt):
    if pd.isna(dt): return "N/A"
    try:
        return pd.to_datetime(dt).strftime('%d-%b-%y')
    except:
        return "N/A"

def smart_get(row, keywords):
    for col in row.index:
        col_clean = str(col).lower().replace(" ", "").replace("-", "").replace("_", "")
        if all(k.lower().replace(" ", "") in col_clean for k in keywords):
            val = row[col]
            return val if pd.notna(val) else "N/A"
    return "N/A"

def to_excel(df):
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    return buffer.getvalue()

# ==============================
# 📂 LOAD DATA
# ==============================
@st.cache_data
def load_data():
    m = pd.read_excel("Master_Data.xlsx")
    f = pd.read_excel("Active_FOC.xlsx")
    s = pd.read_excel("Service_Details.xlsx")

    for d in [m, f, s]:
        d.columns = d.columns.str.strip()

    return m, f, s

master, foc, service = load_data()

# ==============================
# 🏢 SIDEBAR
# ==============================
st.sidebar.title(f"👋 {st.session_state['d_user']}")

menu = ["Machine Search", "📦 FOC List", "⏳ Overdue Service"]
choice = st.sidebar.radio("Menu", menu)

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ==============================
# 🔍 MACHINE SEARCH
# ==============================
if choice == "Machine Search":

    cust_col = next((c for c in master.columns if "customer" in c.lower()), master.columns[0])
    fab_col = next((c for c in master.columns if "fabrication" in c.lower()), master.columns[1])

    st.title("🛠️ DPSAC Tracker")

    c1, c2 = st.columns(2)

    sel_c = c1.selectbox("Customer", ["All"] + sorted(master[cust_col].astype(str).unique()))
    df_f = master if sel_c == "All" else master[master[cust_col] == sel_c]

    sel_f = c2.selectbox("Fabrication", ["Select"] + sorted(df_f[fab_col].astype(str).unique()))

    if sel_f != "Select":

        row = df_f[df_f[fab_col].astype(str) == str(sel_f)].iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        # ==============================
        # BASIC
        # ==============================
        with col1:
            st.markdown("### 📋 Basic Info")
            st.write(f"Customer: {row[cust_col]}")
            st.write(f"HMR: {smart_get(row, ['hmr'])}")
            st.write(f"Last Call: {fmt(smart_get(row, ['last','date']))}")

        # ==============================
        # PART MAP
        # ==============================
        parts = {
            "OIL": ["oil"],
            "AFC": ["afc"],
            "AFE": ["afe"],
            "MOF": ["mof"],
            "ROF": ["rof"],
            "AOS": ["aos"],
            "RGT": ["grease"],
            "1500": ["1500"],
            "3000": ["3000"]
        }

        # ==============================
        # REPLACEMENT
        # ==============================
        with col2:
            st.markdown("### 🔧 Replacement")

            for k, v in parts.items():
                val = smart_get(row, v + ["r"])
                st.write(f"{k}: {fmt(val)}")

        # ==============================
        # REMAINING
        # ==============================
        with col3:
            st.markdown("### ⏳ Remaining")

            for k, v in parts.items():
                val = smart_get(row, v + ["rem"])
                st.write(f"{k}: {val}")

        # ==============================
        # DUE
        # ==============================
        with col4:
            st.markdown("### 🚨 Due")

            for k, v in parts.items():
                val = smart_get(row, v + ["due"])
                st.write(f"{k}: {fmt(val)}")

        # ==============================
        # FOC FILTER
        # ==============================
        st.divider()

        f_fab = next((c for c in foc.columns if "fabrication" in c.lower()), foc.columns[0])

        foc_cols = [c for c in foc.columns if any(k in c.lower() for k in ["fabrication","part","qty","date"])]

        st.subheader("🎁 FOC")
        st.dataframe(
            foc[foc[f_fab].astype(str) == str(sel_f)][foc_cols],
            use_container_width=True
        )

        # ==============================
        # SERVICE
        # ==============================
        s_fab = next((c for c in service.columns if "fabrication" in c.lower()), service.columns[0])

        serv_cols = [c for c in service.columns if any(k in c.lower() for k in ["fabrication","date","hmr","status"])]

        st.subheader("🕒 Service")
        st.dataframe(
            service[service[s_fab].astype(str) == str(sel_f)][serv_cols],
            use_container_width=True
        )

# ==============================
# 📦 FOC LIST
# ==============================
elif choice == "📦 FOC List":
    foc_cols = [c for c in foc.columns if any(k in c.lower() for k in ["fabrication","part","qty","date"])]
    st.dataframe(foc[foc_cols], use_container_width=True)

# ==============================
# ⏳ OVERDUE
# ==============================
elif choice == "⏳ Overdue Service":

    over_col = next((c for c in master.columns if any(k in c.lower() for k in ["over","pending","red"])), None)

    if over_col:
        master[over_col] = pd.to_numeric(master[over_col], errors="coerce").fillna(0)

        overdue_df = master[master[over_col] > 0]

        if not overdue_df.empty:

            show_cols = [c for c in master.columns if any(k in c.lower() for k in [
                "customer","fabrication","status",over_col.lower()
            ])]

            st.dataframe(overdue_df[show_cols], use_container_width=True)

            st.download_button(
                "Download",
                to_excel(overdue_df),
                "Overdue.xlsx"
            )
        else:
            st.success("No overdue machines")
    else:
        st.error("Overdue column not found")
