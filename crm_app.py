import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO
import urllib.parse

st.set_page_config(page_title="ELGi CRM App", layout="wide")

@st.cache_data
def load_data():
    try:
        master = pd.read_excel("Master_Data.xlsx")
        service = pd.read_excel("Service_Details.xlsx")
        return master, service
    except Exception as e:
        st.error(f"Error loading Excel files: {e}")
        return pd.DataFrame(), pd.DataFrame()

master, service = load_data()

# Clean columns
master.columns = master.columns.str.strip()
service.columns = service.columns.str.strip()

def get_col(columns, keywords, default=None):
    for kw in keywords:
        col = next((c for c in columns if kw.lower() in c.lower()), None)
        if col:
            return col
    return default

def to_excel(df):
    buf = BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

# Mapping columns
customer_col = get_col(master.columns, ["customer name", "customer", "customer id"], master.columns[0])
machine_col = get_col(master.columns, ["fabrication no", "fabrication number", "fabrication", "fabrication no."], master.columns[1])
status_col = get_col(master.columns, ["service status", "unit status", "status"])
category_col = get_col(master.columns, ["category", "product sub group", "model group"])
contact_col = get_col(master.columns, ["contact no", "mobile", "phone"])
email_col = get_col(master.columns, ["email", "email id"])
warranty_col = get_col(master.columns, ["warranty expires", "warranty pd", "warranty type", "warranty"])
commission_col = get_col(master.columns, ["comm date", "date of commissioning", "commissioning"])

service_fab_col = get_col(service.columns, ["fabrication number", "fabrication no", "fabrication"])
service_customer_col = get_col(service.columns, ["customer", "customer name"])
service_call_col = get_col(service.columns, ["call logged date", "first visit date", "next visit date"])
service_next_visit_col = get_col(service.columns, ["next visit date", "next visit date & time"])
service_status_col = get_col(service.columns, ["call status", "service status"])
service_engineer_col = get_col(service.columns, ["service engineer", "assigned to"])

# Process Data
master_filtered = master.copy()
if customer_col:
    master_filtered[customer_col] = master_filtered[customer_col].astype(str)

master_filtered["warranty_expires"] = pd.to_datetime(master_filtered[warranty_col], errors="coerce") if warranty_col else pd.NaT
master_filtered["commission_date"] = pd.to_datetime(master_filtered[commission_col], errors="coerce") if commission_col else pd.NaT

service_enriched = service.copy()
service_enriched["call_logged"] = pd.to_datetime(service_enriched[service_call_col], errors="coerce") if service_call_col else pd.NaT
service_enriched["next_visit"] = pd.to_datetime(service_enriched[service_next_visit_col], errors="coerce") if service_next_visit_col else pd.NaT

# Sidebar
st.sidebar.title("ELGi CRM Filters")
cust_list = ["All"] + sorted(master_filtered[customer_col].dropna().unique().tolist()) if customer_col else ["All"]
selected_customer = st.sidebar.selectbox("Select Customer", cust_list)

status_values = ["All"]
if status_col:
    status_values += sorted(master_filtered[status_col].dropna().astype(str).unique())
selected_status = st.sidebar.selectbox("Select Status", status_values)

category_values = ["All"]
if category_col:
    category_values += sorted(master_filtered[category_col].dropna().astype(str).unique())
selected_category = st.sidebar.selectbox("Select Category", category_values)

search_text = st.sidebar.text_input("Search", "")

# Filtering Logic
filtered = master_filtered
if selected_customer != "All" and customer_col:
    filtered = filtered[filtered[customer_col].astype(str) == selected_customer]
if selected_status != "All" and status_col:
    filtered = filtered[filtered[status_col].astype(str) == selected_status]
if selected_category != "All" and category_col:
    filtered = filtered[filtered[category_col].astype(str) == selected_category]
if search_text:
    mask = filtered.apply(lambda row: row.astype(str).str.contains(search_text, case=False, na=False).any(), axis=1)
    filtered = filtered[mask]

# UI Dashboard
st.title("📇 ELGi CRM App")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Customers", filtered[customer_col].nunique() if customer_col else len(filtered))
col2.metric("Machines", filtered[machine_col].nunique() if machine_col else len(filtered))
col3.metric("Warranty Expired", len(filtered[filtered["warranty_expires"] < pd.Timestamp.today()]) if warranty_col else "N/A")

status_counts = pd.Series()
if status_col:
    status_counts = filtered[status_col].dropna().astype(str).value_counts()
    col4.metric("Status Types", len(status_counts))
else:
    col4.metric("Status Types", "N/A")

# Charts Fix
chart_cols = st.columns(2)
if not status_counts.empty:
    df_status = status_counts.reset_index()
    df_status.columns = ['Status', 'Count']
    fig1 = px.bar(df_status, x="Status", y="Count", title="Service Status Breakdown", color="Status")
    chart_cols[0].plotly_chart(fig1, use_container_width=True)

if category_col:
    cat_counts = filtered[category_col].dropna().astype(str).value_counts()
    if not cat_counts.empty:
        df_cat = cat_counts.reset_index()
        df_cat.columns = ['Category', 'Count']
        fig2 = px.pie(df_cat, names="Category", values="Count", title="Category Distribution", hole=0.4)
        chart_cols[1].plotly_chart(fig2, use_container_width=True)

# Data Tables
st.subheader("Customer & Machine Summary")
display_cols = [c for c in [customer_col, machine_col, status_col, category_col, contact_col, email_col] if c is not None]
st.dataframe(filtered[display_cols], use_container_width=True)

# Service Follow-up Fix
st.subheader("Recent Service Requests")
service_view = service_enriched.copy()
rename_map = {service_customer_col: "Customer", service_fab_col: "Fabrication", 
              service_status_col: "Status", service_engineer_col: "Service Engineer"}
service_view = service_view.rename(columns={k: v for k, v in rename_map.items() if k})

display_svc = [c for c in ["Customer", "Fabrication", service_call_col, service_next_visit_col, "Status", "Service Engineer"] if c in service_view.columns and c is not None]

if not service_view.empty and display_svc:
    sort_by = service_next_visit_col if service_next_visit_col in service_view.columns else display_svc[0]
    service_view["sort_key"] = service_view[sort_by].astype(str)
    st.dataframe(service_view.sort_values("sort_key").head(50)[display_svc], use_container_width=True)
else:
    st.info("No service requests found.")

# Export
st.subheader("Export & Outreach")
st.download_button("Download Filtered Data", to_excel(filtered), "crm_data.xlsx")
