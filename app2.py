import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

# ================= LOGIN =================
USER_DB = {
    "admin": {"pass": "admin123"},
    "viewer": {"pass": "demo"}
}

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    st.title("🔐 Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USER_DB and USER_DB[u]["pass"] == p:
            st.session_state["login"] = True
            st.session_state["user"] = u
            st.rerun()
        else:
            st.error("Invalid Login")

    st.stop()

st.sidebar.title(f"👋 {st.session_state['user']}")

# ================= LOAD =================
try:
    df = pd.read_excel("Master_OD_Data.xlsx")
    foc = pd.read_excel("Active_FOC.xlsx")
    service = pd.read_excel("Service_Details.xlsx")
except:
    st.error("❌ Excel file missing")
    st.stop()

df = df.fillna("")
foc = foc.fillna("")
service = service.fillna("")

df.columns = df.columns.str.strip()

# ================= COLUMN SAFE =================
def get_col(keyword):
    return next((c for c in df.columns if keyword in c.lower()), None)

cust_col = get_col("customer")
fab_col = get_col("fabrication")
status_col = get_col("status")
cat_col = get_col("category")
w_col = get_col("warranty")
amc_col = get_col("amc")

red_col = get_col("red")
yellow_col = get_col("yellow")
green_col = get_col("green")

if cust_col is None or fab_col is None:
    st.error("❌ Required columns missing (Customer/Fabrication)")
    st.stop()

# ================= FILTER =================
df[cust_col] = df[cust_col].astype(str)
df[fab_col] = df[fab_col].astype(str)

customers = ["All"] + sorted(df[cust_col].unique())
sel = st.sidebar.selectbox("Customer", customers)

df_f = df if sel == "All" else df[df[cust_col] == sel]

# ================= SIDEBAR =================
st.sidebar.subheader("📊 Unit Count")
if status_col:
    st.sidebar.write(df_f[status_col].value_counts())

if cat_col:
    st.sidebar.subheader("📊 Category Count")
    st.sidebar.write(df_f[cat_col].value_counts())

# ================= DASHBOARD =================
st.title("🏭 Industrial Dashboard")

st.metric("Total Units", len(df_f))

if status_col:
    active = len(df_f[df_f[status_col].str.contains("active", case=False)])
    st.metric("Active Units", active)

# ================= HEALTH =================
st.subheader("🚦 Health")

col1, col2, col3 = st.columns(3)

col1.metric("Red", int(pd.to_numeric(df_f.get(red_col, 0), errors='coerce').sum()))
col2.metric("Yellow", int(pd.to_numeric(df_f.get(yellow_col, 0), errors='coerce').sum()))
col3.metric("Green", int(pd.to_numeric(df_f.get(green_col, 0), errors='coerce').sum()))

# ================= WARRANTY =================
st.sidebar.subheader("📅 Warranty Monthly")

if w_col:
    df_f[w_col] = pd.to_datetime(df_f[w_col], errors='coerce')
    df_f["Warranty End"] = df_f[w_col] + pd.DateOffset(years=1)

    year = st.sidebar.selectbox("Year", [2023, 2024, 2025, 2026])

    df_w = df_f[df_f["Warranty End"].dt.year == year]

    st.sidebar.write(df_w["Warranty End"].dt.month.value_counts().sort_index())

# ================= AMC =================
st.sidebar.subheader("📆 AMC Expired")

if amc_col:
    df_f[amc_col] = pd.to_datetime(df_f[amc_col], errors='coerce')

    df_amc = df_f[df_f[amc_col] < datetime.today()]

    st.sidebar.write(df_amc[amc_col].dt.month.value_counts().sort_index())

# ================= MACHINE =================
st.subheader("🔍 Machine Tracker")

machines = ["Select"] + list(df_f[fab_col].unique())
sel_f = st.selectbox("Fabrication", machines)

if sel_f != "Select":

    data = df_f[df_f[fab_col] == sel_f]

    if data.empty:
        st.warning("No data found")
    else:
        row = data.iloc[0]
        st.dataframe(pd.DataFrame([row]))

        # FOC
        foc_col = next((c for c in foc.columns if "fabrication" in c.lower()), None)

        if foc_col:
            st.subheader("🎁 FOC")
            st.dataframe(foc[foc[foc_col] == sel_f])

        # SERVICE
        srv_col = next((c for c in service.columns if "fabrication" in c.lower()), None)

        if srv_col:
            st.subheader("🛠 Service History")
            st.dataframe(service[service[srv_col] == sel_f])