import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO
import urllib.parse

st.set_page_config(page_title="ELGi CRM App", layout="wide")

@st.cache(allow_output_mutation=True)
def load_data():
    master = pd.read_excel("Master_Data.xlsx")
    service = pd.read_excel("Service_Details.xlsx")
    return master, service

master, service = load_data()
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

master_filtered = master.copy()

if customer_col:
    master_filtered[customer_col] = master_filtered[customer_col].astype(str)

# parse date fields
if warranty_col:
    master_filtered["warranty_expires"] = pd.to_datetime(master_filtered[warranty_col], errors="coerce")
else:
    master_filtered["warranty_expires"] = pd.NaT

if commission_col:
    master_filtered["commission_date"] = pd.to_datetime(master_filtered[commission_col], errors="coerce")
else:
    master_filtered["commission_date"] = pd.NaT

service_enriched = service.copy()
if service_call_col:
    service_enriched["call_logged"] = pd.to_datetime(service_enriched[service_call_col], errors="coerce")
else:
    service_enriched["call_logged"] = pd.NaT

if service_next_visit_col:
    service_enriched["next_visit"] = pd.to_datetime(service_enriched[service_next_visit_col], errors="coerce")
else:
    service_enriched["next_visit"] = pd.NaT

# sidebar filters
st.sidebar.title("ELGi CRM Filters")
selected_customer = st.sidebar.selectbox(
    "Select Customer",
    ["All"] + sorted(master_filtered[customer_col].dropna().astype(str).unique()) if customer_col else ["All"],
)

status_values = ["All"]
if status_col:
    status_values += sorted(master_filtered[status_col].dropna().astype(str).unique())
selected_status = st.sidebar.selectbox("Select Status", status_values)

category_values = ["All"]
if category_col:
    category_values += sorted(master_filtered[category_col].dropna().astype(str).unique())
selected_category = st.sidebar.selectbox("Select Category", category_values)

search_text = st.sidebar.text_input("Search", "")

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

# dashboard layout
st.title("📇 ELGi CRM App")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Customers", filtered[customer_col].nunique() if customer_col else len(filtered))
col2.metric("Machines", filtered[machine_col].nunique() if machine_col else len(filtered))
if warranty_col:
    expired = filtered[filtered["warranty_expires"] < pd.Timestamp.today()]
    col3.metric("Warranty Expired", len(expired))
else:
    col3.metric("Warranty Expired", "N/A")

if status_col:
    status_counts = filtered[status_col].dropna().astype(str).value_counts()
    col4.metric("Status Types", len(status_counts))
else:
    col4.metric("Status Types", "N/A")

# charts
chart_cols = st.columns(2)

if status_col:
    # Use the status_counts we calculated earlier in the metrics section
    status_counts = filtered[status_col].dropna().astype(str).value_counts()
    df_status = status_counts.reset_index()
    df_status.columns = ['Status', 'Count']
    
    status_chart = px.bar(
        df_status, 
        x="Status", 
        y="Count", 
        title="Service Status Breakdown",
        color="Status"
    )
    chart_cols[0].plotly_chart(status_chart, use_container_width=True)

if category_col:
    # Explicitly define category_counts right before using it to avoid NameError
    category_counts = filtered[category_col].dropna().astype(str).value_counts()
    df_category = category_counts.reset_index()
    df_category.columns = ['Category', 'Count']
    
    category_chart = px.pie(
        df_category, 
        names="Category", 
        values="Count", 
        title="Category Distribution",
        hole=0.4
    )
    chart_cols[1].plotly_chart(category_chart, use_container_width=True)# data tables
st.subheader("Customer & Machine Summary")
st.dataframe(filtered[[c for c in [customer_col, machine_col, status_col, category_col, contact_col, email_col] if c is not None]], use_container_width=True)

st.subheader("Overdue & Warranty Alerts")
alert_cols = []
if warranty_col:
    alert_cols.append("warranty_expires")
if "Over Due" in master_filtered.columns:
    alert_cols.append("Over Due")
elif "Overdue" in master_filtered.columns:
    alert_cols.append("Overdue")

alerts = master_filtered.copy()
if "warranty_expires" in alerts.columns:
    alerts = alerts[alerts["warranty_expires"].notna() & (alerts["warranty_expires"] <= pd.Timestamp.today())]
if "Over Due" in alerts.columns:
    alerts = alerts[pd.to_numeric(alerts["Over Due"], errors="coerce").fillna(0) > 0]
elif "Overdue" in alerts.columns:
    alerts = alerts[pd.to_numeric(alerts["Overdue"], errors="coerce").fillna(0) > 0]

if not alerts.empty:
    st.dataframe(alerts[[c for c in [customer_col, machine_col, status_col, category_col, "warranty_expires", "Over Due", "Overdue"] if c in alerts.columns]], use_container_width=True)
else:
    st.info("No overdue warranty or service items found.")

# service follow-up list
st.subheader("Recent Service Requests")
service_view = service_enriched.copy()

if service_customer_col:
    service_view = service_view.rename(columns={service_customer_col: "Customer"})
if service_fab_col:
    service_view = service_view.rename(columns={service_fab_col: "Fabrication"})
if service_status_col:
    service_view = service_view.rename(columns={service_status_col: "Status"})
if service_engineer_col:
    service_view = service_view.rename(columns={service_engineer_col: "Service Engineer"})

# Define which columns we want to show
service_display_cols = [c for c in ["Customer", "Fabrication", service_call_col, service_next_visit_col, "Status", "Service Engineer"] if c in service_view.columns]

if not service_view.empty and service_display_cols:
    # Determine sorting column: prioritize next visit date if it exists
    sort_col = service_next_visit_col if service_next_visit_col in service_view.columns else service_display_cols[0]
    
    # Sort and display
    sorted_service = service_view[service_display_cols].sort_values(by=sort_col, ascending=True).head(50)
    st.dataframe(sorted_service, use_container_width=True)
else:
    st.info("No recent service requests found or columns missing in 'Service_Details.xlsx'.")
# customer detail view
st.sidebar.header("Customer Detail")
if selected_customer != "All" and customer_col:
    customer_row = filtered[filtered[customer_col].astype(str) == selected_customer].head(1)
    if not customer_row.empty:
        st.sidebar.markdown(f"**Customer:** {selected_customer}")
        if contact_col:
            st.sidebar.markdown(f"**Contact:** {customer_row.iloc[0].get(contact_col, 'N/A')}")
        if email_col:
            st.sidebar.markdown(f"**Email:** {customer_row.iloc[0].get(email_col, 'N/A')}")
        if warranty_col:
            st.sidebar.markdown(f"**Warranty Expires:** {customer_row.iloc[0].get('warranty_expires', 'N/A')}")
        if machine_col:
            st.sidebar.markdown(f"**Machine:** {customer_row.iloc[0].get(machine_col, 'N/A')}")

# export and quick action
st.subheader("Export & Customer Outreach")
col_a, col_b = st.columns(2)
col_a.download_button("Download Filtered CRM Data", to_excel(filtered), "crm_data.xlsx")

message = st.text_area("WhatsApp Message", "Hello, this is your ELGi service team. Please review the upcoming service follow-up for your machine.")
if col_b.button("Create WhatsApp Link"):
    phone = str(customer_row.iloc[0].get(contact_col, "")) if selected_customer != "All" and contact_col else ""
    if phone:
        link = f"https://wa.me/{phone.replace('+','').replace(' ','')}?text={urllib.parse.quote(message)}"
        st.markdown(f"[Send WhatsApp Message]({link})")
    else:
        st.warning("No phone number available for the selected customer.")
