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

selected_machine = st.sidebar.selectbox("Track Machine (Fabrication No.)", machine_list)

# Dashboard Title
st.title("📇 PRIME POWER CRM App")

# Filtering Logic
filtered_master = master.copy()
if selected_customer != "All":
    filtered_master = filtered_master[filtered_master[customer_col] == selected_customer]
if selected_machine != "All":
    filtered_master = filtered_master[filtered_master[machine_col] == selected_machine]

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Customers", filtered_master[customer_col].nunique())
col2.metric("Total Machines", filtered_master[machine_col].nunique())
col3.metric("Current Selection", selected_machine if selected_machine != "All" else "Multiple")

# --- SECTION 1: RECENT SERVICE REQUESTS (Tracked Machine Only) ---
st.subheader("🛠️ Recent Service Requests")

if selected_machine != "All" and service_fab_col:
    # Machine ke basis par filter karna
    svc_filtered = service[service[service_fab_col].astype(str) == str(selected_machine)].copy()
    
    if not svc_filtered.empty:
        # Aapke bataye gaye columns ko map karna
        # Note: Columns ke naam aapki file ke hisab se exact hone chahiye (e.g., 'Call Logged Date' or 'Service Engineer Comment')
        svc_display_cols = ["Call Logged Date", "Call Type", "Call HMR"]
        
        # Check karna ki columns file mein hain ya nahi
        existing_svc_cols = [c for c in svc_display_cols if c in svc_filtered.columns]
        comment_col = "Service Engineer Comment" # Ya "Remarks" / "Engineer Remarks"
        
        # Table display karna (sirf a, b, c columns ke liye)
        st.dataframe(svc_filtered[existing_svc_cols], use_container_width=True)
        
        # d) Service Engineer Comment (Jo click hone par expand hoga)[cite: 1]
        if comment_col in svc_filtered.columns:
            with st.expander("💬 View Service Engineer Comments"):
                # Har ek service visit ke liye comment dikhana[cite: 1]
                for index, row in svc_filtered.iterrows():
                    date_val = row.get("Call Logged Date", "N/A")
                    comment_val = row.get(comment_col, "No comments provided.")
                    st.markdown(f"**Date: {date_val}**")
                    st.info(comment_val)
                    st.divider()
        else:
            st.info("Note: 'Service Engineer Comment' column not found in file.")
            
    else:
        st.info(f"No recent service records found for machine: {selected_machine}")
else:
    st.warning("Please select a specific Machine to view Service History.")

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
