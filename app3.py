import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table

st.set_page_config(layout="wide")

# ================= LOGIN =================
USER_DB = {"admin": "admin123", "viewer": "demo"}

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
df = pd.read_excel("Master_OD_Data.xlsx").fillna("")
df.columns = df.columns.str.strip()

# ================= COLUMN =================
def get_col(keyword):
    return next((c for c in df.columns if keyword.lower() in c.lower()), None)

cust_col = get_col("customer")
fab_col = get_col("fabrication")
status_col = get_col("status")
cat_col = get_col("category")
w_col = get_col("warranty")
amc_col = get_col("amc")
priority_col = get_col("priority Visits")
visit_col = get_col("visit")
model_col = get_col("model")
loc_col = get_col("location")
contact_col = get_col("contact")

# ================= FILTER =================
df[cust_col] = df[cust_col].astype(str)
df[fab_col] = df[fab_col].astype(str)

customers = ["All"] + sorted(df[cust_col].unique())
sel = st.sidebar.selectbox("Customer", customers)

df_f = df if sel == "All" else df[df[cust_col] == sel]

# ================= EXPORT =================
def to_excel(df):
    buf = BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

def to_pdf(df):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf)
    data = [df.columns.tolist()] + df.astype(str).values.tolist()
    table = Table(data)
    doc.build([table])
    return buf.getvalue()

# ================= DASHBOARD =================
st.sidebar.subheader("📅 Warranty Expiry (Monthly)")

if w_col:
    df[w_col] = pd.to_datetime(df[w_col], errors='coerce')
    df["Warranty End"] = df[w_col] + pd.DateOffset(years=1)

    df_w = df.dropna(subset=["Warranty End"])

    if not df_w.empty:
        year = st.sidebar.selectbox(
            "Warranty Year",
            sorted(df_w["Warranty End"].dt.year.unique()),
            key="w_year"
        )

        df_wy = df_w[df_w["Warranty End"].dt.year == year]

        monthly_w = df_wy["Warranty End"].dt.month.value_counts().sort_index()

        st.sidebar.write(monthly_w)
        
# ================= AMC =================
st.sidebar.subheader("📆 AMC Expiry (Monthly)")

if amc_col:
    df[amc_col] = pd.to_datetime(df[amc_col], errors='coerce')

    df_a = df.dropna(subset=[amc_col])

    if not df_a.empty:
        year_a = st.sidebar.selectbox(
            "AMC Year",
            sorted(df_a[amc_col].dt.year.unique()),
            key="a_year"
        )

        df_ay = df_a[df_a[amc_col].dt.year == year_a]

        monthly_a = df_ay[amc_col].dt.month.value_counts().sort_index()

        st.sidebar.write(monthly_a)
        st.download_button("AMC Excel", to_excel(df_amc))
        st.download_button("AMC PDF", to_pdf(df_amc))

# ================= MACHINE TRACKER =================
st.subheader("🔍 Machine Tracker")

machines = ["Select"] + list(df_f[fab_col].unique())
sel_f = st.selectbox("Select Machine", machines)

if sel_f != "Select":

    data = df_f[df_f[fab_col] == sel_f]

    if not data.empty:
        row = data.iloc[0]
        st.dataframe(pd.DataFrame([row]))

        st.subheader("🔧 Parts")

        parts = ["AF","OF","OIL","AOS","RGT","VK","PF","FF","CF"]

        for part in parts:

            rep_col = next((c for c in df.columns if part.lower() in c.lower() and "r date" in c.lower()), None)
            rem_col = next((c for c in df.columns if part.lower() in c.lower() and "rem" in c.lower()), None)
            due_col = next((c for c in df.columns if part.lower() in c.lower() and "due" in c.lower()), None)

            rep = row.get(rep_col, "N/A")
            rem = row.get(rem_col, "N/A")
            due = row.get(due_col, "N/A")

            st.write(f"{part} → R: {rep} | Rem: {rem} | Due: {due}")

# ================= PRIORITY =================
st.subheader("🚨 Priority Visit Dashboard")

if priority_col:

    p_df = df_f[df_f[priority_col].astype(str).str.strip() != ""]

    if not p_df.empty:

        st.success(f"{len(p_df)} Priority Visits Found")

        st.dataframe(p_df[[c for c in [
            fab_col, cust_col, model_col, loc_col,
            contact_col, visit_col, priority_col
        ] if c in p_df.columns]], use_container_width=True)

    else:
        st.warning("No Priority Visit Data")
        
# ================= CHART =================
if status_col:
    st.subheader("📊 Status Chart")

    vc = df_f[status_col].value_counts().reset_index()
    vc.columns = ["Status", "Count"]

    fig = px.pie(vc, names="Status", values="Count")
    st.plotly_chart(fig)
