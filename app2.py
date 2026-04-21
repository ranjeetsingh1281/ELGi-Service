import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table

st.set_page_config(layout="wide")

# ================= LOAD =================
df = pd.read_excel("Master_OD_Data.xlsx").fillna("")
foc = pd.read_excel("Active_FOC.xlsx").fillna("")
service = pd.read_excel("Service_Details.xlsx").fillna("")

df.columns = df.columns.str.strip()
foc.columns = foc.columns.str.strip()
service.columns = service.columns.str.strip()

# ================= COLUMN FIND =================
def get_col(df, keyword):
    return next((c for c in df.columns if keyword.lower() in c.lower()), None)

cust_col = get_col(df, "customer")
fab_col = get_col(df, "fabrication")
connect_col = get_col(df, "connect_status")
cat_col = get_col(df, "sub category")
w_col = get_col(df, "warranty")
amc_col = get_col(df, "amc")

# ================= FILTER =================
df[cust_col] = df[cust_col].astype(str)

customers = ["All"] + sorted(df[cust_col].unique())
sel = st.sidebar.selectbox("Customer", customers)

df_f = df if sel == "All" else df[df[cust_col] == sel]

# ================= EXPORT =================
def to_excel(data):
    buf = BytesIO()
    data.to_excel(buf, index=False)
    return buf.getvalue()

def to_pdf(data):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf)
    table = Table([data.columns.tolist()] + data.astype(str).values.tolist())
    doc.build([table])
    return buf.getvalue()

# ================= DASHBOARD =================
st.title("🏭 Industrial Dashboard")
st.metric("Total Units", len(df_f))

# ================= SIDEBAR =================
if connect_col:
    st.sidebar.subheader("📊 Unit Status")
    st.sidebar.write(df_f[connect_col].value_counts())

if cat_col:
    st.sidebar.subheader("📊 Category")
    st.sidebar.write(df_f[cat_col].value_counts())

# ================= WARRANTY =================
st.sidebar.subheader("📅 Warranty Monthly")

if w_col:
    df[w_col] = pd.to_datetime(df[w_col], errors='coerce')
    df["Warranty End"] = df[w_col] + pd.DateOffset(years=1)

    df_w = df.dropna(subset=["Warranty End"])

    if not df_w.empty:
        year = st.sidebar.selectbox("Warranty Year", sorted(df_w["Warranty End"].dt.year.unique()))
        df_wy = df_w[df_w["Warranty End"].dt.year == year]

        st.sidebar.write(df_wy["Warranty End"].dt.month.value_counts().sort_index())

# ================= AMC =================
st.sidebar.subheader("📆 AMC Monthly")

if amc_col:
    df[amc_col] = pd.to_datetime(df[amc_col], errors='coerce')

    df_a = df.dropna(subset=[amc_col])

    if not df_a.empty:
        year_a = st.sidebar.selectbox("AMC Year", sorted(df_a[amc_col].dt.year.unique()))
        df_ay = df_a[df_a[amc_col].dt.year == year_a]

        st.sidebar.write(df_ay[amc_col].dt.month.value_counts().sort_index())

# ================= MACHINE TRACKER =================
st.subheader("🔍 Machine Tracker")

machines = ["Select"] + list(df_f[fab_col].unique())
sel_f = st.selectbox("Select Machine", machines)

if sel_f != "Select":

    row = df_f[df_f[fab_col] == sel_f].iloc[0]
    st.dataframe(pd.DataFrame([row]))

    # ================= PARTS =================
    st.subheader("🔧 Parts")

    parts = ["AF","OF","OIL","AOS","RGT","VK","PF","FF","CF"]

    for part in parts:
        rem_col = next((c for c in df.columns if part.lower() in c.lower() and "rem" in c.lower()), None)
        due_col = next((c for c in df.columns if part.lower() in c.lower() and "due" in c.lower()), None)

        rem = row.get(rem_col, "")
        due = row.get(due_col, "")

        st.write(f"{part} → Remaining: {rem} | Due: {due}")

    # ================= SERVICE HISTORY =================
    st.subheader("📜 Service History")

    fab_service_col = get_col(service, "fabrication")

    if fab_service_col:
        service_f = service[service[fab_service_col].astype(str) == sel_f]

        if not service_f.empty:
            show_cols = [
                get_col(service, "call date"),
                get_col(service, "call no"),
                get_col(service, "call type"),
                get_col(service, "engineer"),
                get_col(service, "status")
            ]

            show_cols = [c for c in show_cols if c]

            st.dataframe(service_f[show_cols])
        else:
            st.info("No Service History Found")

    # ================= FOC =================
    st.subheader("📦 FOC Details")

    fab_foc_col = get_col(foc, "fabrication")

    if fab_foc_col:
        foc_f = foc[foc[fab_foc_col].astype(str) == sel_f]

        if not foc_f.empty:
            show_cols = [
                get_col(foc, "foc"),
                get_col(foc, "work order"),
                get_col(foc, "customer"),
                get_col(foc, "type"),
                get_col(foc, "status"),
                get_col(foc, "model"),
                get_col(foc, "fabrication"),
                get_col(foc, "failure"),
                get_col(foc, "part"),
                get_col(foc, "qty")
            ]

            show_cols = [c for c in show_cols if c]

            st.dataframe(foc_f[show_cols])
        else:
            st.info("No FOC Data Found")

# ================= CHART =================
st.subheader("📊 Unit Status Chart")

if connect_col:
    fig = px.pie(df_f, names=connect_col)
    st.plotly_chart(fig, use_container_width=True)

# ================= WHATSAPP =================
st.subheader("📲 WhatsApp Alert")

if st.button("Send Alert"):
    st.success("✅ Alert Sent (Demo)")
