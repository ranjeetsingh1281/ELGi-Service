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
# ================= KPI COUNTS (MASTER आधारित) =================

overdue_col = get_col(df,"over due")
curr_col   = get_col(df,"current month due")
next_col   = get_col(df,"next month due")

def count_flag(series):
    
    s = series.astype(str).str.strip().str.lower()

    return s.isin([
        "1",
        "1.0",
        "yes",
        "y",
        "true"
    ]).sum()

overdue_count = count_flag(df_f[overdue_col]) if overdue_col else 0
current_month_count = count_flag(df_f[curr_col]) if curr_col else 0
next_month_count = count_flag(df_f[next_col]) if next_col else 0

# ================= DISPLAY =================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Units", len(df_f))
col2.metric("Overdue", overdue_count)
col3.metric("Current Month Due", current_month_count)
col4.metric("Next Month Due", next_month_count)

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

# 🔥 DIRECT COLUMN NAME (CHANGE IF NEEDED)
amc_status_col = "AMC Status"

if amc_status_col in df.columns:

    df[amc_status_col] = df[amc_status_col].astype(str).str.strip().str.lower()

    def map_status(x):
        if "expire" in x:
            return "Expired"
        elif "not" in x:
            return "Not in AMC"
        elif "amc" in x:
            return "AMC"
        elif x == "" or x == "nan":
            return "Blank"
        else:
            return "Blank"

    df["AMC Clean"] = df[amc_status_col].apply(map_status)

    order = ["AMC", "Expired", "Not in AMC", "Blank"]

    amc_counts = df["AMC Clean"].value_counts().reindex(order, fill_value=0)

    st.sidebar.write(amc_counts)

else:
    st.sidebar.error("AMC Status column not found ❌")
    
# ================= CLICKABLE OVERDUE =================

if overdue_col:

    st.markdown("### ⚠️ Overdue Units")

    flag_mask = (
        df_f[overdue_col]
        .astype(str)
        .str.strip()
        .isin(["1","1.0"])
    )

    overdue_df = df_f[flag_mask]

    if not overdue_df.empty:

        st.success(
            f"{len(overdue_df)} Overdue Units Found"
        )

        fab_col = get_col(df,"fabrication")

        machines = (
            overdue_df[fab_col]
            .astype(str)
            .unique()
        )

        sel_machine = st.selectbox(
            "Select Overdue Machine",
            machines,
            key="overdue_machine_select"
        )

        if sel_machine:

            row = overdue_df[
                overdue_df[fab_col].astype(str)==sel_machine
    ]

   # ================= PREMIUM MACHINE CARD =================

def fmt_date(v):
    try:
        d = pd.to_datetime(v, errors="coerce")
        if pd.isna(d):
            return "-"
        return d.strftime("%d-%b-%y")
    except:
        return "-"

r = row.iloc[0]

# helper
def pick(col_hint):
    c = get_col(df, col_hint)
    return r.get(c,"-") if c else "-"


# -------- COLUMN GROUPS --------

customer_items = [
    ("Customer", pick("customer")),
    ("Model", pick("model")),
    ("Location", pick("location")),
]

replacement_items = [
    ("AF", fmt_date(pick("AF R Date"))),
    ("OF", fmt_date(pick("OF R Date"))),
    ("OIL", fmt_date(pick("Oil R Date"))),
    ("AOS", fmt_date(pick("AOS R Date"))),
    ("RGT", fmt_date(pick("RGT R Date"))),
    ("Valve", fmt_date(pick("Valvekit R Date"))),
    ("PF", fmt_date(pick("PF R DATE"))),
    ("FF", fmt_date(pick("FF R DATE"))),
    ("CF", fmt_date(pick("CF R DATE"))),
]

hours_items = [
    ("AF", pick("AF Rem")),
    ("OF", pick("OF Rem")),
    ("OIL", pick("OIL Rem")),
    ("AOS", pick("AOS Rem")),
    ("VK", pick("VK Rem")),
    ("RGT", pick("RGT Rem")),
]

due_items = [
    ("AF", fmt_date(pick("AF DUE DATE"))),
    ("OF", fmt_date(pick("OF DUE DATE"))),
    ("OIL", fmt_date(pick("OIL DUE DATE"))),
    ("AOS", fmt_date(pick("AOS DUE DATE"))),
    ("VK", fmt_date(pick("VALVEKIT DUE DATE"))),
    ("RGT", fmt_date(pick("RGT DUE DATE"))),
    ("PF", fmt_date(pick("PF DUE DATE"))),
    ("FF", fmt_date(pick("FF DUE DATE"))),
    ("CF", fmt_date(pick("CF DUE DATE"))),
]


# -------- DISPLAY --------

c1,c2,c3,c4 = st.columns(4)

with c1:
    st.markdown("### 👤 Customer Info")
    for k,v in customer_items:
        st.write(f"**{k}:** {v}")

with c2:
    st.markdown("### 🔧 Replacement Dates")
    for k,v in replacement_items:
        st.write(f"{k}: {v}")

with c3:
    st.markdown("### ⏳ Remaining Hours")
    for k,v in hours_items:
        st.write(f"{k}: {v}")

with c4:
    st.markdown("### 📅 Due Dates")
    for k,v in due_items:
        st.write(f"{k}: {v}")

    curr_col = get_col(df,"current month due")
    next_col = get_col(df,"next month due")

    ov = str(row[overdue_col].iloc[0]).strip()
    cm = str(row[curr_col].iloc[0]).strip() if curr_col else "0"
    nm = str(row[next_col].iloc[0]).strip() if next_col else "0"

    if ov in ["1","1.0"]:
        st.error("🔴 PRIORITY RED : OVERDUE")

    elif cm in ["1","1.0"]:
        st.warning("🟠 PRIORITY AMBER : CURRENT MONTH DUE")

    elif nm in ["1","1.0"]:
        st.success("🟢 PRIORITY GREEN : NEXT MONTH DUE")

    else:
        st.info("⚪ NORMAL")

else:
    st.warning("Over Due column not found")


            
# ================= MACHINE TRACKER =================
st.subheader("🔍 Machine Tracker")

machines = ["Select"] + list(df_f[fab_col].unique())
sel_f = st.selectbox(
    "Select Machine",
    machines,
    key="main_machine_tracker"
)

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
