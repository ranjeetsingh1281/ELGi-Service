#=============== Working as on 29-04-2026=================#
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
if st.button("🔄 Refresh Data"):
    st.rerun()
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
#============== Alert Banner (top warning) =================#
if overdue_count > 0:

    st.error(
      f"⚠ {overdue_count} Overdue Units Need Attention"
    )
else:
    st.success(
      "✔ No overdue units"
    )

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
        st.download_button(
            label="⬇ Download Overdue List",
            data=overdue_df.to_csv(index=False),
            file_name="Overdue_Units.csv",
            mime="text/csv"
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
        
cust_col  = get_col(df, "Customer Name")
model_col = get_col(df, "Model")
loc_col   = get_col(df, "Location")

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
    st.metric("Total Units", len(df))

with c2:
    if overdue_count > 0:
        st.error(f"🔴 Overdue\n{overdue_count}")
    else:
        st.success("No Overdue")

with c3:
    st.warning(f"🟠 Current Month\n{current_month_count}")

with c4:
    st.success(f"🟢 Next Month\n{next_month_count}")
    
    curr_col = get_col(df,"current month due")
    next_col = get_col(df,"next month due")

    ov = str(r[overdue_col]).strip()
    cm = str(r[curr_col]).strip() if curr_col else "0"
    nm = str(r[next_col]).strip() if next_col else "0"

    if ov in ["1","1.0"]:
        st.error("🔴 PRIORITY RED : OVERDUE")

    elif cm in ["1","1.0"]:
        st.warning("🟠 PRIORITY AMBER : CURRENT MONTH DUE")

    elif nm in ["1","1.0"]:
        st.success("🟢 PRIORITY GREEN : NEXT MONTH DUE")

    else:
        st.info("⚪ NORMAL")

#================ Smart Search (top search box)=================#

st.subheader("🔎 Smart Search")

search = st.text_input(
    "Search by Fabrication / Customer / Model"
)

if search:

    result = df_f[
        df_f.astype(str)
        .apply(
            lambda x: x.str.contains(
                search,
                case=False,
                na=False
            )
        ).any(axis=1)
    ]

    if not result.empty:
        st.write("Search Results")
        st.dataframe(result.head(20))

    else:
        st.warning("No matching record found")
        
# ================= MACHINE TRACKER =================
st.subheader("🔍 Machine Tracker")

machines = ["Select"] + list(df_f[fab_col].astype(str).unique())

sel_f = st.selectbox(
    "Select Machine",
    machines,
    key="main_machine_tracker"
)

if sel_f != "Select":

    # selected row
    row = df_f[
        df_f[fab_col].astype(str) == str(sel_f)
    ].iloc[0]

    # export button (INDENTED inside IF)
    report_row = pd.DataFrame([row])

    st.download_button(
        "⬇ Download Machine Report",
        report_row.to_csv(index=False),
        file_name=f"{sel_f}_Machine_Report.csv",
        mime="text/csv"
    )

    # show raw record
    st.dataframe(pd.DataFrame([row]))

    r = row

    def pick(h):
        c = get_col(df,h)
        return r.get(c,"-") if c else "-"
        
    # ================= MACHINE TRACKER PREMIUM CARD =================

a,b,c,d = st.columns(4)

    with a:
        st.markdown("### 👤 Customer Info")
        st.write(f"Customer: {pick('customer')}")
        st.write(f"Model: {pick('model')}")
        st.write(f"Location: {pick('location')}")

    with b:
        st.markdown("### 🔧 Replacement Dates")

        for p in [
            "AF R Date","OF R Date","Oil R Date",
            "AOS R Date","RGT R Date",
            "Valvekit R Date",
            "PF R DATE","FF R DATE","CF R DATE"
        ]:
            st.write(f"{p}: {fmt_date(pick(p))}")


    with c:
        st.markdown("### ⏳ Remaining Hours")

        for p in [
            "AF Rem. HMR Till date",
            "OF Rem. HMR Till date",
            "OIL Rem. HMR Till date",
            "AOS Rem. HMR Till date",
            "VK Rem. HMR Till date",
            "RGT Rem. HMR Till date"
        ]:
            v = pick(p)

            try:
                hrs = float(v)

                if hrs < 0:
                    st.error(f"{p}: {hrs}")

                elif hrs < 500:
                    st.warning(f"{p}: {hrs}")

                else:
                    st.success(f"{p}: {hrs}")

            except:
                st.write(f"{p}: -")


    with d:
        st.markdown("### 📅 Due Dates")

        for p in [
            "AF DUE DATE","OF DUE DATE","OIL DUE DATE",
            "AOS DUE DATE","VALVEKIT DUE DATE",
            "RGT DUE DATE","PF DUE DATE",
            "FF DUE DATE","CF DUE DATE"
        ]:
            try:
                due_dt = pd.to_datetime(pick(p))

                if due_dt < pd.Timestamp.today():
                    st.error(f"{p}: {fmt_date(due_dt)}")

                elif due_dt <= pd.Timestamp.today()+pd.Timedelta(days=30):
                    st.warning(f"{p}: {fmt_date(due_dt)}")

                else:
                    st.success(f"{p}: {fmt_date(due_dt)}")

            except:
                st.write(f"{p}: -")

    #==============Service Trend Chart==============#
call_date_col=get_col(service,"Call Logged Date")

if call_date_col:

    svc=service.copy()

    svc[call_date_col]=pd.to_datetime(
        svc[call_date_col],
        errors="coerce"
    )

    svc["Month"]=svc[call_date_col].dt.strftime("%b-%y")

    trend=svc.groupby("Month").size()

    if len(trend)>0:

        st.subheader("📈 Service Trend")

        st.line_chart(trend)
        
# ================= PIE CHART =================
st.subheader("📊 Unit Status Chart")

if connect_col:
    allowed = ["Within 3 months","Above 3 months","P1",""]
    df_chart = df_f[df_f[connect_col].isin(allowed)].copy()
    df_chart[connect_col] = df_chart[connect_col].replace("", "Blank")

    fig = px.pie(df_chart, names=connect_col)
    st.plotly_chart(fig, use_container_width=True)
