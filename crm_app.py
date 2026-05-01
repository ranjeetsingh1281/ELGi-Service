import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO
import urllib.parse

st.set_page_config(page_title="PRIME POWER CRM App", layout="wide")

@st.cache_data
def load_data():
    try:
        master = pd.read_excel("Master_Data.xlsx")
        service = pd.read_excel("Service_Details.xlsx")
        foc = pd.read_excel("Active_FOC.xlsx") # Nayi file link ki gayi hai
        return master, service, foc
    except Exception as e:
        st.error(f"Error loading Excel files: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

master, service, foc = load_data()

# Clean columns
for df in [master, service, foc]:
    if not df.empty:
        df.columns = df.columns.str.strip()

def get_col(columns, keywords, default=None):
    for kw in keywords:
        col = next((c for c in columns if kw.lower() in c.lower()), None)
        if col:
            return col
    return default

# Mapping columns
customer_col = get_col(master.columns, ["customer name", "customer", "customer id"], master.columns[0])
machine_col = get_col(master.columns, ["fabrication no", "fabrication number", "fabrication"], master.columns[1])
status_col = get_col(master.columns, ["service status", "unit status", "status"])
category_col = get_col(master.columns, ["category", "product sub group", "model group"])
contact_col = get_col(master.columns, ["contact no", "mobile", "phone"])

service_fab_col = get_col(service.columns, ["fabrication number", "fabrication no", "fabrication"])
foc_fab_col = get_col(foc.columns, ["fabrication no.", "fabrication no", "fabrication"]) # FOC file ke liye

# Sidebar Filters
st.sidebar.title("CRM Filters")
selected_customer = st.sidebar.selectbox("Select Customer", ["All"] + sorted(master[customer_col].dropna().unique().tolist()))

# Machine Selection (Tracking)
# Jab aap ek specific machine select karenge, tabhi Service aur FOC details filter honge
machine_list = ["All"]
if selected_customer != "All":
    machine_list += sorted(master[master[customer_col] == selected_customer][machine_col].dropna().unique().tolist())
else:
    machine_list += sorted(master[machine_col].dropna().unique().tolist())

selected_machine = st.sidebar.selectbox("Fabrication No.", machine_list)

# Dashboard Title
# --- DASHBOARD START ---
st.title("📇 PRIME POWER CRM App")

# 1. Top Metrics (Total Customers, Machines & Unit Status)
# --- Metrics Section Fix ---
col1, col2, col3, col4 = st.columns(4)

# Dhayan dein: yahan 'col1' hona chahiye, 'coll' nahi
col1.metric("Total Customers", filtered_master[customer_col].nunique() if customer_col else 0)
col2.metric("Total Machines", filtered_master[machine_col].nunique() if machine_col else 0)

if "Unit Status" in filtered_master.columns:
    status_counts = filtered_master["Unit Status"].value_counts()
    col3.metric("Running Units", status_counts.get("Running", 0))
    col4.metric("Breakdown Units", status_counts.get("Breakdown", 0))
else:
    col3.metric("Running", "N/A")
    col4.metric("Breakdown", "N/A")
st.markdown("---")

# 2. 4-Column Machine Tracker (Sirf tab dikhega jab Machine select hogi)
st.subheader(f"🔍 Machine Detailed Tracker")

if selected_machine != "All":
    # Selected machine ka data filter karna
    m_data = master[master[machine_col].astype(str) == str(selected_machine)].iloc[0]
    
    # 4 Columns layout setup
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.info("👤 Customer Info")
        # Column 1: Customer Details
        st.write(f"**Customer:** {m_data.get('CUSTOMER NAME', 'N/A')}")
        st.write(f"**Address:** {m_data.get('Address', 'N/A')}")
        st.write(f"**Email:** {m_data.get('EMAIL ID', 'N/A')}")
        st.write(f"**Contact:** {m_data.get('Contact No. 1', 'N/A')}")
        st.write(f"**Last Service Date:** {m_data.get('Last Service Date', 'N/A')}")
        st.write(f"**Last Service HMR:** {m_data.get('Last Service HMR', 'N/A')}")
        st.write(f"**Avg. Hrs:** {m_data.get('Avg. Hrs', '0')}")
        st.write(f"**HMR Cal.:** {m_data.get('HMR Cal.', 'N/A')}")

    with c2:
        st.warning("📅 Last Replacement")
        # Column 2: R Dates
        r_cols = ["Oil R Date", "AFC R Date", "AFE R Date", "MOF R Date", "ROF R Date", "AOS R Date", "RGT R Date", "1500 kit R Date", "3000 kit R Date"]
        for col in r_cols:
            st.write(f"**{col}:** {m_data.get(col, 'N/A')}")

    with c3:
        st.success("⏳ LIVE Remaining")
        # Column 3: Remaining Hours
        live_cols = ["LIVE - Oil remaining", "LIVE - Air filter replaced - Compressor Remaining Hours", 
                     "LIVE - Air filter replaced - Engine Remaining Hours", "LIVE - Main Oil filter Remaining Hours", 
                     "LIVE - Return Oil filter Remaining Hours", "LIVE - Separator remaining", 
                     "LIVE - Motor regressed remaining", "LIVE - 1500 Valve kit Remaining Hours", 
                     "LIVE - 3000 Valve kit Remaining Hours"]
        for col in live_cols:
            st.write(f"**{col}:** {m_data.get(col, '0')}")

    with c4:
        st.error("🚨 Next Due Dates")
        # Column 4: Due Dates
        due_cols = ["OIL DUE DATE", "AFC DUE DATE", "AFE DUE DATE", "MOF DUE DATE", "ROF DUE DATE", "AOS DUE DATE", "RGT DUE DATE", "1500 KIT DUE DATE", "3000 KIT DUE DATE"]
        for col in due_cols:
            st.write(f"**{col}:** {m_data.get(col, 'N/A')}")
else:
    st.info("Sidebar se koi Machine select karein full details dekhne ke liye.")

st.markdown("---")
# Iske niche aapka Recent Service Request aur FOC wala code rahega.
    
# --- SECTION 2: FOC DETAILS (Tracked Machine Only) ---
st.subheader("📦 FOC Details")
if selected_machine != "All" and foc_fab_col:
    foc_filtered = foc[foc[foc_fab_col].astype(str) == str(selected_machine)]
    
    # Aapke bataye gaye columns ko display karna
    foc_display_cols = [
        "Created On", "FOC Number", "Work Order Number", "Customer Name", 
        "FOC Type", "MODEL", "FABRICATION NO.", "Failure Material Details", 
        "Part Code", "ELGI IVOICE NO."
    ]
    
    # Check if columns exist in the file
    existing_cols = [c for c in foc_display_cols if c in foc.columns]
    
    if not foc_filtered.empty:
        st.dataframe(foc_filtered[existing_cols], use_container_width=True)
    else:
        st.info(f"No FOC details found for machine: {selected_machine}")
else:
    st.warning("Please select a specific Machine to view FOC Details.")

# Master Data Summary
st.subheader("📋 Machine Master Summary")
st.dataframe(filtered_master, use_container_width=True)
