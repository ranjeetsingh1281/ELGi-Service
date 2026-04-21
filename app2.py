import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from io import BytesIO

st.set_page_config(layout="wide")

# ================= LOAD =================
df = pd.read_excel("Master_OD_Data.xlsx").fillna("")
foc = pd.read_excel("Active_FOC.xlsx").fillna("")
service = pd.read_excel("Service_Details.xlsx").fillna("")

df.columns = df.columns.str.strip()
foc.columns = foc.columns.str.strip()
service.columns = service.columns.str.strip()

# ================= DATE FORMAT =================
def fmt_date(val):
    try:
        dt = pd.to_datetime(val, errors='coerce')
        if pd.isna(dt):
            return ""
        return dt.strftime("%d-%b-%y")
    except:
        return str(val)

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
st.sidebar.subheader("📅 Warranty Expiry (Monthly)")

w_end_col = get_col(df, "warranty end")

if w_end_col:

    df[w_end_col] = pd.to_datetime(df[w_end_col], errors='coerce')

    df_w = df.dropna(subset=[w_end_col])

    if not df_w.empty:

        years = sorted(df_w[w_end_col].dt.year.dropna().unique())

        year = st.sidebar.selectbox("Warranty Year", years)

        df_wy = df_w[df_w[w_end_col].dt.year == year]

        monthly = df_wy.groupby(df_wy[w_end_col].dt.month).size()

        # 👉 Month name convert (premium look)
        monthly.index = monthly.index.map(lambda x: pd.to_datetime(str(x), format="%m").strftime("%b"))

        st.sidebar.write(monthly)
# ================= AMC =================
st.sidebar.subheader("📆 AMC Status Summary")

amc_status_col = get_col(df, "amc status")

if amc_status_col:

    # Normalize values
    df[amc_status_col] = df[amc_status_col].astype(str).str.strip().str.lower()

    # Mapping (clean categories)
    def map_status(x):
        if "expire" in x:
            return "Expired"
        elif "amc" in x:
            return "AMC"
        elif "not" in x:
            return "Not in AMC"
        else:
            return "Blank"

    df["AMC Clean"] = df[amc_status_col].apply(map_status)

    amc_counts = df["AMC Clean"].value_counts()

    st.sidebar.write(amc_counts)

st.sidebar.subheader("📅 AMC Expired (Monthly)")

amc_date_col = get_col(df, "amc")

if amc_status_col and amc_date_col:

    df[amc_date_col] = pd.to_datetime(df[amc_date_col], errors='coerce')

    # 👉 Only Expired
    df_exp = df[df["AMC Clean"] == "Expired"].dropna(subset=[amc_date_col])

    if not df_exp.empty:

        years = sorted(df_exp[amc_date_col].dt.year.unique())

        year = st.sidebar.selectbox("AMC Year", years)

        df_year = df_exp[df_exp[amc_date_col].dt.year == year]

        monthly = df_year.groupby(df_year[amc_date_col].dt.month).size()

        # Month name
        monthly.index = monthly.index.map(
            lambda x: pd.to_datetime(str(x), format="%m").strftime("%b")
        )

        st.sidebar.write(monthly)
# ================= MACHINE TRACKER =================
st.subheader("🔍 Machine Tracker")

machines = ["Select"] + list(df_f[fab_col].unique())
sel_f = st.selectbox("Select Machine", machines)

if sel_f != "Select":

    row = df_f[df_f[fab_col] == sel_f].iloc[0]
    st.dataframe(pd.DataFrame([row]))

    # ================= PARTS =================
    st.subheader("🔧 Parts Full Details")

    # Replacement
    st.markdown("### 🔁 Replacement Dates")
    replacement_cols = [
        "Oil R Date","AF R Date","OF R Date","AOS R Date","RGT R Date",
        "Valvekit R Date","PF R DATE","FF R DATE","CF R DATE"
    ]

    for col in replacement_cols:
        c = get_col(df, col)
        if c:
            st.write(f"{col} → {fmt_date(row.get(c,''))}")

    # Remaining
    st.markdown("### ⏳ Remaining Hours")
    remaining_cols = [
        "AF Rem","OF Rem","OIL Rem","AOS Rem","VK Rem","RGT Rem"
    ]

    for col in remaining_cols:
        c = get_col(df, col)
        if c:
            val = row.get(c, "")
            color = "🟢"
            try:
                if float(val) < 200:
                    color = "🔴"
                elif float(val) < 500:
                    color = "🟡"
            except:
                pass

            st.write(f"{color} {col} → {val}")

    # Due Dates
    st.markdown("### 📅 Due Dates")
    due_cols = [
        "AF DUE","OF DUE","OIL DUE","AOS DUE","VALVEKIT DUE",
        "RGT DUE","PF DUE","FF DUE","CF DUE"
    ]

    for col in due_cols:
        c = get_col(df, col)
        if c:
            due = row.get(c, "")
            overdue = ""

            try:
                if pd.to_datetime(due, errors='coerce') < pd.Timestamp.today():
                    overdue = "⚠️ OVERDUE"
            except:
                pass

            st.write(f"{col} → {fmt_date(due)} {overdue}")

    # ================= SERVICE =================
    st.subheader("📜 Service History")

    fab_service_col = get_col(service, "fabrication")

    if fab_service_col:
        service_f = service[service[fab_service_col].astype(str) == sel_f]

        if not service_f.empty:
            for col in service_f.columns:
                if "date" in col.lower():
                    service_f[col] = service_f[col].apply(fmt_date)

            st.dataframe(service_f)
        else:
            st.info("No Service History Found")

    # ================= FOC =================
    st.subheader("📦 FOC Details")

    fab_foc_col = get_col(foc, "fabrication")

    if fab_foc_col:
        foc_f = foc[foc[fab_foc_col].astype(str) == sel_f]

        if not foc_f.empty:
            for col in foc_f.columns:
                if "date" in col.lower():
                    foc_f[col] = foc_f[col].apply(fmt_date)

            st.dataframe(foc_f)
        else:
            st.info("No FOC Data Found")

# ================= PIE CHART =================
st.subheader("📊 Unit Status Chart")

if connect_col:
    allowed = ["Within 3 months","Above 3 months","P1",""]
    df_chart = df_f[df_f[connect_col].isin(allowed)].copy()
    df_chart[connect_col] = df_chart[connect_col].replace("", "Blank")

    fig = px.pie(df_chart, names=connect_col)
    st.plotly_chart(fig, use_container_width=True)
