import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="PRIME POWER CRM App", layout="wide")

@st.cache_data
def load_data():
    try:
        master = pd.read_excel("Master_Data.xlsx")
        service = pd.read_excel("Service_Details.xlsx")
        foc = pd.read_excel("Active_FOC.xlsx")
        return master, service, foc
    except Exception as e:
        st.error(f"Error loading Excel files: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

master, service, foc = load_data()

# Helper: Date formatting dd-mmm-yy
def format_date(val):
    if pd.isna(val) or val == "N/A" or str(val).strip() == "":
        return "N/A"
    try:
        return pd.to_datetime(val).strftime('%d-%b-%y')
    except:
        return str(val)

# Helper: Smart Column Detection
def find_column(df, keywords):
    for col in df.columns:
        if any(kw.lower() in str(col).lower() for kw in keywords):
            return col
    return None

# Clean columns
for df in [master, service, foc]:
    if not df.empty:
        df.columns = df.columns.str.strip()

# --- SIDEBAR FILTERS ---
st.sidebar.title("CRM Filters")

customer_col = find_column(master, ["customer name", "customer"]) or "CUSTOMER NAME"
machine_col = find_column(master, ["fabrication", "fab no"]) or "FABRICATION NO."
category_col = find_column(master, ["category", "model group"]) or "Category"

if category_col in master.columns:
    cat_list = ["All"] + sorted(master[category_col].dropna().unique().tolist())
    selected_category = st.sidebar.selectbox("Select Category", cat_list)
    if selected_category != "All":
        master = master[master[category_col] == selected_category]

cust_list = ["All"] + sorted(master[customer_col].dropna().unique().tolist())
selected_customer = st.sidebar.selectbox("Select Customer", cust_list)

filtered_master = master.copy()
if selected_customer != "All":
    filtered_master = filtered_master[filtered_master[customer_col] == selected_customer]

machine_list = ["All"] + sorted(filtered_master[machine_col].dropna().astype(str).unique().tolist())
selected_machine = st.sidebar.selectbox("Track Machine (Fabrication No.)", machine_list)

# --- DASHBOARD START ---
st.title("📇 PRIME POWER CRM App")

# 1) Metrics Section
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Customers", filtered_master[customer_col].nunique())
col2.metric("Total Machines", filtered_master[machine_col].nunique())

if "Unit Status" in filtered_master.columns:
    status_counts = filtered_master["Unit Status"].value_counts()
    col3.metric("Running Units", status_counts.get("Running", 0))
    col4.metric("Breakdown Units", status_counts.get("Breakdown", 0))
else:
    col3.metric("Running", "N/A")
    col4.metric("Breakdown", "N/A")

st.markdown("---")

# 2) 4-Column Tracker (dd-mmm-yy format applied)
if selected_machine != "All":
    m_data = master[master[machine_col].astype(str) == str(selected_machine)].iloc[0]
    st.subheader(f"🔍 Detailed Tracker: {selected_machine}")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.info("👤 Customer Info")
        st.write(f"**Customer:** {m_data.get('CUSTOMER NAME', 'N/A')}")
        st.write(f"**Address:** {m_data.get('Address', 'N/A')}")
        st.write(f"**Email:** {m_data.get('EMAIL ID', 'N/A')}")
        st.write(f"**Contact:** {m_data.get('Contact No. 1', 'N/A')}")
        st.write(f"**Last Service Date:** {format_date(m_data.get('Last Service Date'))}")
        st.write(f"**Last Service HMR:** {m_data.get('Last Service HMR', 'N/A')}")
        st.write(f"**Avg. Hrs:** {m_data.get('Avg. Hrs', '0')}")
        st.write(f"**HMR Cal.:** {m_data.get('HMR Cal.', 'N/A')}")

    with c2:
        st.warning("📅 Last Replacement")
        for col in ["Oil R Date", "AFC R Date", "AFE R Date", "MOF R Date", "ROF R Date", "AOS R Date", "RGT R Date", "1500 kit R Date", "3000 kit R Date"]:
            st.write(f"**{col}:** {format_date(m_data.get(col))}")

    with c3:
        st.success("⏳ LIVE Remaining")
        for col in ["LIVE - Oil remaining", "LIVE - Air filter replaced - Compressor Remaining Hours", "LIVE - Air filter replaced - Engine Remaining Hours", "LIVE - Main Oil filter Remaining Hours", "LIVE - Return Oil filter Remaining Hours", "LIVE - Separator remaining", "LIVE - Motor regressed remaining", "LIVE - 1500 Valve kit Remaining Hours", "LIVE - 3000 Valve kit Remaining Hours"]:
            st.write(f"**{col}:** {m_data.get(col, '0')}")

    with c4:
        st.error("🚨 Next Due Dates")
        for col in ["OIL DUE DATE", "AFC DUE DATE", "AFE DUE DATE", "MOF DUE DATE", "ROF DUE DATE", "AOS DUE DATE", "RGT DUE DATE", "1500 KIT DUE DATE", "3000 KIT DUE DATE"]:
            st.write(f"**{col}:** {format_date(m_data.get(col))}")
else:
    st.info("Sidebar se machine select karein full details ke liye.")

st.markdown("---")

# 3) Recent Service Requests (Filtered)
st.subheader("🛠️ Recent Service Requests")
svc_fab_col = find_column(service, ["fabrication"])
service_display = service.copy()

if selected_machine != "All" and svc_fab_col:
    service_display = service_display[service_display[svc_fab_col].astype(str) == str(selected_machine)]

if not service_display.empty:
    for _, row in service_display.head(10).iterrows():
        label = f"📅 {format_date(row.get('Call Logged Date'))} | Type: {row.get('Call Type','N/A')} | HMR: {row.get('Call HMR','N/A')}"
        with st.expander(label):
            st.info(row.get("Service Engineer Comments", "No comments."))
else:
    st.info("Service record nahi mila.")

st.markdown("---")

# 4) FOC Details (Filtered)
st.subheader("📦 FOC Details")
foc_fab_col = find_column(foc, ["fabrication"])
foc_display = foc.copy()

if selected_machine != "All" and foc_fab_col:
    foc_display = foc_display[foc_display[foc_fab_col].astype(str) == str(selected_machine)]

foc_cols = ["Created On", "FOC Number", "Work Order Number", "Customer Name", "FOC Type", "MODEL", "FABRICATION NO.", "Failure Material Details", "Part Code", "ELGI IVOICE NO."]
existing_foc = [c for c in foc_cols if c in foc_display.columns]

if not foc_display.empty:
    st.dataframe(foc_display[existing_foc], use_container_width=True)
else:
    st.info("FOC record nahi mila.")
