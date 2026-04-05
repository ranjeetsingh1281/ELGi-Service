import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

st.set_page_config(layout="wide")

# ================= LOGIN =================
USER_DB = {
    "admin": "admin123",
    "viewer": "demo"
}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USER_DB and USER_DB[u] == p:
            st.session_state.login = True
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Invalid Login")

    st.stop()

st.sidebar.title(f"👋 {st.session_state.user}")

# ================= LOAD =================
try:
    df = pd.read_excel("Master_OD_Data.xlsx").fillna("")
    foc = pd.read_excel("Active_FOC.xlsx").fillna("")
    service = pd.read_excel("Service_Details.xlsx").fillna("")
except Exception as e:
    st.error(f"❌ Error loading files: {e}")
    st.stop()

df.columns = df.columns.str.strip()
foc.columns = foc.columns.str.strip()
service.columns = service.columns.str.strip()

# ================= COLUMN FIND =================
def get_col(keyword):
    return next((c for c in df.columns if keyword.lower() in c.lower()), None)

cust_col = get_col("customer")
fab_col = get_col("fabrication")
status_col = get_col("status")
cat_col = get_col("category")
w_col = get_col("warranty")
amc_col = get_col("amc")

# ================= VALIDATION =================
if cust_col is None or fab_col is None:
    st.error("❌ Required columns missing (Customer / Fabrication)")
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

def sum_col(col):
    return int(pd.to_numeric(df_f.get(col, 0), errors='coerce').sum())

c1, c2, c3 = st.columns(3)

c1.metric("🔴 Red", sum_col(get_col("red")))
c2.metric("🟡 Yellow", sum_col(get_col("yellow")))
c3.metric("🟢 Green", sum_col(get_col("green")))

# ================= WARRANTY =================
st.sidebar.subheader("📅 Warranty Monthly")

if w_col:
    df_f[w_col] = pd.to_datetime(df_f[w_col], errors='coerce')
    df_f["Warranty End"] = df_f[w_col] + pd.DateOffset(years=1)

    df_valid = df_f.dropna(subset=["Warranty End"])

    if not df_valid.empty:
        year = st.sidebar.selectbox("Year", sorted(df_valid["Warranty End"].dt.year.unique()))
        df_year = df_valid[df_valid["Warranty End"].dt.year == year]

        st.sidebar.write(df_year["Warranty End"].dt.month.value_counts().sort_index())

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

        # ================= PARTS =================
        st.subheader("🔧 Parts Dashboard")

        parts = []

        for col in df.columns:
            if "rem" in col.lower():
                parts.append(col.split()[0])

        parts = list(set(parts))

        for part in sorted(parts):

            rem_col = next((c for c in df.columns if part.lower() in c.lower() and "rem" in c.lower()), None)
            due_col = next((c for c in df.columns if part.lower() in c.lower() and "due" in c.lower()), None)

            rem_val = row.get(rem_col, None)
            due_val = row.get(due_col, None)

            color = "🟢"

            try:
                rem_val = float(rem_val)
                if rem_val < 200:
                    color = "🔴"
                elif rem_val < 500:
                    color = "🟡"
            except:
                pass

            overdue = ""
            try:
                if pd.to_datetime(due_val, errors='coerce') < pd.Timestamp.today():
                    overdue = "⚠️ OVERDUE"
            except:
                pass

            st.write(f"{color} {part} → Remaining: {rem_val} | Due: {due_val} {overdue}")

        # ================= FOC =================
        foc_col = next((c for c in foc.columns if "fabrication" in c.lower()), None)

        if foc_col:
            foc_cols = ["Created on","FOC No","Part No","Description","FOC Status","ELGi Invoice No"]
            st.subheader("🎁 FOC List")
            st.dataframe(foc[foc[foc_col]==sel_f][[c for c in foc_cols if c in foc.columns]])

        # ================= SERVICE =================
        srv_col = next((c for c in service.columns if "fabrication" in c.lower()), None)

        if srv_col:
            srv_cols = ["Created on","Call No","HMR","Call Type","Service Engineer Comments"]
            st.subheader("🛠 Service History")
            st.dataframe(service[service[srv_col]==sel_f][[c for c in srv_cols if c in service.columns]])

# ================= CHART =================
st.subheader("📊 Unit Status Chart")

if status_col:
    fig = px.pie(df_f, names=status_col)
    st.plotly_chart(fig, use_container_width=True)

# ================= AI =================
st.subheader("🤖 AI Assistant")

q = st.text_input("Ask something")

if st.button("Ask AI"):
    if q:
        st.success(f"👋 {q}")
    else:
        st.warning("Enterprises question")