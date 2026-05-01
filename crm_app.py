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

# Clean columns
for df in [master, service, foc]:
    if not df.empty:
        df.columns = df.columns.str.strip()

# Sidebar Filters
st.sidebar.title("CRM Filters")
customer_col = "CUSTOMER NAME" if "CUSTOMER NAME" in master.columns else master.columns[0]
machine_col = "FABRICATION NO." if "FABRICATION NO." in master.columns else master.columns[1]

# Sidebar Category Filter
if "Category" in master.columns:
    cat_list = ["All"] + sorted(master["Category"].dropna().unique().tolist())
    selected_category = st.sidebar.selectbox("Select Category", cat_list)
    if selected_category != "All":
        master = master[master["Category"] == selected_category]

selected_customer = st.sidebar.selectbox("Select Customer", ["All"] + sorted(master[customer_col].dropna().unique().tolist()))

# Machine selection logic
filtered_master = master.copy()
if selected_customer != "All":
    filtered_master = master[master[customer_col] == selected_customer]

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

# 2) 4-Column Machine Tracker (Displays only when a machine is tracked)
if selected_machine != "All":
    m_data = master[master[machine_col].astype(str) == str(selected_machine)].iloc[0]
    st.subheader(f"🔍 Detailed Tracker: {selected_machine}")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.info("👤 Customer Info")
        cols1 = ["CUSTOMER NAME", "Address", "EMAIL ID", "Contact No. 1", "Last Service Date", "Last Service HMR", "Avg. Hrs", "HMR Cal."]
        for col in cols1: st.write(f"**{col}:** {m_data.get(col, 'N/A')}")
    with c2:
        st.warning("📅 Last Replacement")
        cols2 = ["Oil R Date", "AFC R Date", "AFE R Date", "MOF R Date", "ROF R Date", "AOS R Date", "RGT R Date", "1500 kit R Date", "3000 kit R Date"]
        for col in cols2: st.write(f"**{col}:** {m_data.get(col, 'N/A')}")
    with c3:
        st.success("⏳ LIVE Remaining")
        cols3 = ["LIVE - Oil remaining", "LIVE - Air filter replaced - Compressor Remaining Hours", "LIVE - Air filter replaced - Engine Remaining Hours", "LIVE - Main Oil filter Remaining Hours", "LIVE - Return Oil filter Remaining Hours", "LIVE - Separator remaining", "LIVE - Motor regressed remaining", "LIVE - 1500 Valve kit Remaining Hours", "LIVE - 3000 Valve kit Remaining Hours"]
        for col in cols3: st.write(f"**{col}:** {m_data.get(col, '0')}")
    with c4:
        st.error("🚨 Next Due Dates")
        cols4 = ["OIL DUE DATE", "AFC DUE DATE", "AFE DUE DATE", "MOF DUE DATE", "ROF DUE DATE", "AOS DUE DATE", "RGT DUE DATE", "1500 KIT DUE DATE", "3000 KIT DUE DATE"]
        for col in cols4: st.write(f"**{col}:** {m_data.get(col, 'N/A')}")
else:
    st.info("Sidebar se koi Machine select karein details dekhne ke liye.")

st.markdown("---")

# 3) Recent Service Requests (Always visible, filtered if machine selected)
st.subheader("🛠️ Recent Service Requests")
svc_fab_col = next((c for c in service.columns if "fabrication" in c.lower()), None)
service_display = service.copy()

if selected_machine != "All" and svc_fab_col:
    service_display = service_display[service_display[svc_fab_col].astype(str) == str(selected_machine)]

if not service_display.empty:
    if "Call Logged Date" in service_display.columns:
        service_display = service_display.sort_values(by="Call Logged Date", ascending=False)
    
    for _, row in service_display.head(10).iterrows():
        exp_label = f"📅 {row.get('Call Logged Date','N/A')} | Type: {row.get('Call Type','N/A')} | HMR: {row.get('Call HMR','N/A')}"
        with st.expander(exp_label):
            st.info(row.get("Service Engineer Comments", "No comments."))
else:
    st.info("Koi service record nahi mila.")

st.markdown("---")

# 4) FOC Details (Always visible, filtered if machine selected)
st.subheader("📦 FOC Details")
foc_fab_col = next((c for c in foc.columns if "fabrication" in c.lower()), None)
foc_display = foc.copy()

if selected_machine != "All" and foc_fab_col:
    foc_display = foc_display[foc_display[foc_fab_col].astype(str) == str(selected_machine)]

foc_cols = ["Created On", "FOC Number", "Work Order Number", "Customer Name", "FOC Type", "MODEL", "FABRICATION NO.", "Failure Material Details", "Part Code", "ELGI IVOICE NO."]
existing_foc = [c for c in foc_cols if c in foc_display.columns]

if not foc_display.empty:
    st.dataframe(foc_display[existing_foc], use_container_width=True)
else:
    st.info("Koi FOC record nahi mila.")
