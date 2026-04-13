import pandas as pd
import streamlit as st
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="ELGi Service App", layout="wide")

USER_DB = {"admin": "admin123", "viewer": "demo"}
PARTS = ["AF", "OF", "OIL", "AOS", "RGT", "VK", "PF", "FF", "CF"]


@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    data = pd.read_excel(path).fillna("")
    data.columns = (
        data.columns.astype(str).str.strip().str.replace("\n", "", regex=False).str.replace("\r", "", regex=False)
    )
    return data


def get_col(df: pd.DataFrame, keyword: str):
    return next((c for c in df.columns if keyword.lower() in c.lower()), None)


def to_excel(data: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    data.to_excel(buffer, index=False)
    return buffer.getvalue()


def score_priority(last_visit_value) -> str:
    last_visit = pd.to_datetime(last_visit_value, errors="coerce")
    if pd.isna(last_visit):
        return "Unknown"

    days = (datetime.today() - last_visit).days
    if days > 60:
        return "🔴 High"
    if days > 30:
        return "🟡 Medium"
    return "🟢 Normal"


if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 ELGi Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if USER_DB.get(username) == password:
            st.session_state.login = True
            st.session_state.user = username
            st.rerun()
        st.error("Invalid Login")
    st.stop()

st.sidebar.title(f"👋 {st.session_state.user}")

try:
    df = load_data("Master_OD_Data.xlsx")
except FileNotFoundError:
    st.error("Master_OD_Data.xlsx not found in project root.")
    st.stop()

cust_col = get_col(df, "customer")
fab_col = get_col(df, "fabrication")
model_col = get_col(df, "model")
loc_col = get_col(df, "location")
contact_col = get_col(df, "contact")
visit_col = get_col(df, "visit")
priority_col = get_col(df, "priority visits")
warranty_col = get_col(df, "warranty")
amc_col = get_col(df, "amc")

if not cust_col or not fab_col:
    st.error("Required columns not found. Please ensure Customer and Fabrication columns exist.")
    st.stop()

df[cust_col] = df[cust_col].astype(str).str.strip()
customers = ["All"] + sorted([x for x in df[cust_col].unique() if x])
selected_customer = st.sidebar.selectbox("Customer", customers)

df_filtered = df if selected_customer == "All" else df[df[cust_col] == selected_customer]

st.title("🏭 ELGi Service Dashboard")
col1, col2, col3 = st.columns(3)
col1.metric("Total Units", len(df_filtered))
col2.metric("Unique Customers", df_filtered[cust_col].nunique())
col3.metric("Priority Visits", int((df_filtered[priority_col].astype(str).str.strip() != "").sum()) if priority_col else 0)

st.sidebar.subheader("📅 Warranty Monthly")
if warranty_col:
    warranty_dates = pd.to_datetime(df[warranty_col], errors="coerce")
    warranty_end = (warranty_dates + pd.DateOffset(years=1)).dropna()
    warranty_years = sorted(warranty_end.dt.year.unique())
    if warranty_years:
        selected_warranty_year = st.sidebar.selectbox("Warranty Year", warranty_years)
        monthly_counts = warranty_end[warranty_end.dt.year == selected_warranty_year].dt.month.value_counts().sort_index()
        st.sidebar.bar_chart(monthly_counts)
    else:
        st.sidebar.info("No valid warranty dates found.")
else:
    st.sidebar.info("Warranty column not found.")

st.sidebar.subheader("📆 AMC Monthly")
if amc_col:
    amc_dates = pd.to_datetime(df[amc_col], errors="coerce").dropna()
    amc_years = sorted(amc_dates.dt.year.unique())
    if amc_years:
        selected_amc_year = st.sidebar.selectbox("AMC Year", amc_years)
        monthly_amc = amc_dates[amc_dates.dt.year == selected_amc_year].dt.month.value_counts().sort_index()
        st.sidebar.bar_chart(monthly_amc)
    else:
        st.sidebar.info("No valid AMC dates found.")
else:
    st.sidebar.info("AMC column not found.")

st.subheader("🚨 Priority Visit Dashboard")
if priority_col:
    priority_df = df_filtered[df_filtered[priority_col].astype(str).str.strip() != ""].copy()
    if not priority_df.empty:
        if visit_col:
            priority_df["Priority Score"] = priority_df[visit_col].apply(score_priority)
        else:
            priority_df["Priority Score"] = "Unknown"

        display_columns = [
            fab_col,
            cust_col,
            model_col,
            loc_col,
            contact_col,
            visit_col,
            priority_col,
            "Priority Score",
        ]
        safe_columns = [c for c in display_columns if c and c in priority_df.columns]
        priority_display = priority_df[safe_columns].copy().astype(str)

        st.success(f"{len(priority_display)} priority visits found.")
        st.dataframe(priority_display, use_container_width=True)
        st.download_button(
            "📥 Download Priority Excel",
            data=to_excel(priority_display),
            file_name="priority_visits.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        if st.button("📲 Send WhatsApp Alerts"):
            st.success("Alerts queued (Demo Mode).")
    else:
        st.info("No priority visit data for selected filters.")
else:
    st.info("Priority visit column not found.")

st.subheader("🔍 Machine Tracker")
machines = ["Select"] + sorted([x for x in df_filtered[fab_col].astype(str).unique() if x])
selected_machine = st.selectbox("Select Machine", machines)

if selected_machine != "Select":
    machine_df = df_filtered[df_filtered[fab_col].astype(str) == selected_machine]
    if machine_df.empty:
        st.warning("Machine not found for selected filters.")
    else:
        machine_row = machine_df.iloc[0]
        st.dataframe(pd.DataFrame([machine_row]), use_container_width=True)
        st.subheader("🔧 Parts Details")

        for part in PARTS:
            rep_col = next((c for c in df.columns if part.lower() in c.lower() and "r date" in c.lower()), None)
            rem_col = next((c for c in df.columns if part.lower() in c.lower() and "rem" in c.lower()), None)
            due_col = next((c for c in df.columns if part.lower() in c.lower() and "due" in c.lower()), None)

            rep_val = machine_row.get(rep_col, "N/A")
            rem_val = machine_row.get(rem_col, "N/A")
            due_val = machine_row.get(due_col, "N/A")

            indicator = "🟢"
            rem_num = pd.to_numeric(rem_val, errors="coerce")
            if pd.notna(rem_num):
                if rem_num < 200:
                    indicator = "🔴"
                elif rem_num < 500:
                    indicator = "🟡"

            overdue = ""
            due_date = pd.to_datetime(due_val, errors="coerce")
            if pd.notna(due_date) and due_date.date() < datetime.today().date():
                overdue = "⚠️ OVERDUE"

            st.write(f"{indicator} {part} → R: {rep_val} | Rem: {rem_val} | Due: {due_val} {overdue}")
