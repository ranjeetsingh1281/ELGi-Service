import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

# ================= LOGIN =================
USER_DB = {"admin": "admin123"}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if USER_DB.get(u) == p:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Invalid Login")

    st.stop()

# ================= LOAD =================
df = pd.read_excel("Master_OD_Data.xlsx").fillna("")
df.columns = df.columns.str.strip()

# ================= COLUMN FIND =================
def get_col(keyword):
    return next((c for c in df.columns if keyword.lower() in c.lower()), None)

cust_col = get_col("customer")
fab_col = get_col("fabrication")
priority_col = get_col("priority visits")
visit_col = get_col("visit")

# ================= FILTER =================
df[cust_col] = df[cust_col].astype(str)
customers = ["All"] + sorted(df[cust_col].unique())

sel = st.sidebar.selectbox("Customer", customers)
df_f = df if sel == "All" else df[df[cust_col] == sel]

# ================= DASHBOARD =================
st.title("🏭 Industrial Dashboard")
st.metric("Total Units", len(df_f))

# ================= PRIORITY =================
st.subheader("🚨 Priority Visit Dashboard")

if priority_col:

    p_df = df_f[df_f[priority_col].astype(str).str.strip() != ""]

    if len(p_df) > 0:

        st.success(f"{len(p_df)} Priority Visits Found")

        p_df = p_df.copy()

        def score(row):
            last = pd.to_datetime(row.get(visit_col), errors='coerce')

            if pd.isna(last):
                return "Unknown"

            days = (datetime.today() - last).days

            if days > 60:
                return "🔴 High"
            elif days > 30:
                return "🟡 Medium"
            else:
                return "🟢 Normal"

        if visit_col:
            p_df["Score"] = p_df.apply(score, axis=1)

        safe_cols = []

        for c in [fab_col, cust_col, visit_col, priority_col, "Score"]:
            if c and c in p_df.columns:
                safe_cols.append(c)

        st.dataframe(p_df[safe_cols], use_container_width=True)

    else:
        st.warning("No Priority Visit Data")

# ================= MACHINE TRACKER =================
st.subheader("🔍 Machine Tracker")

machines = ["Select"] + list(df_f[fab_col].unique())
sel_f = st.selectbox("Machine", machines)

if sel_f != "Select":

    data = df_f[df_f[fab_col] == sel_f]

    if len(data) > 0:
        row = data.iloc[0]
        st.dataframe(pd.DataFrame([row]))
