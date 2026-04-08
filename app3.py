import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

st.set_page_config(layout="wide")

# ================= LOGIN =================
USER_DB = {
    "admin": "admin123",
    "viewer": "demo"
}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USER_DB and USER_DB[u] == p:
            st.session_state.login = True
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Invalid login")

    st.stop()

st.sidebar.title(f"👋 {st.session_state.user}")

# ================= LOAD =================
df = pd.read_excel("Master_OD_Data.xlsx").fillna("")
df.columns = df.columns.str.strip()

# ================= COLUMN FIND =================
def get_col(keyword):
    return next((c for c in df.columns if keyword.lower() in c.lower()), None)

cust_col = get_col("customer")
fab_col = get_col("fabrication")
model_col = get_col("model")
loc_col = get_col("location")
contact_col = get_col("contact")
visit_col = get_col("visit")
priority_col = get_col("priority")

# ================= FILTER =================
df[cust_col] = df[cust_col].astype(str)

customers = ["All"] + sorted(df[cust_col].unique())
sel = st.sidebar.selectbox("Customer", customers)

df_f = df if sel == "All" else df[df[cust_col] == sel]

# ================= DASHBOARD =================
st.title("🏭 Industrial Dashboard")

st.metric("Total Units", len(df_f))

# ================= PRIORITY VISIT =================
st.subheader("🚨 Priority Visit Dashboard")

if priority_col:
    priority_df = df_f[df_f[priority_col].astype(str).str.contains("high", case=False)]

    if not priority_df.empty:

        # DATE HANDLING
        today = pd.Timestamp.today()
        current_month = today.month
        next_month = (today + pd.DateOffset(months=1)).month

        def overdue_status(row):
            last_visit = pd.to_datetime(row.get(visit_col), errors='coerce')
            if pd.isna(last_visit):
                return "Unknown"

            if last_visit < today - pd.Timedelta(days=30):
                return "Overdue"
            return "OK"

        priority_df["Overdue"] = priority_df.apply(overdue_status, axis=1)

        priority_df["Current Month Overdue"] = priority_df.apply(
            lambda x: "Yes" if pd.to_datetime(x.get(visit_col), errors='coerce').month == current_month else "No",
            axis=1
        )

        priority_df["Next Month Overdue"] = priority_df.apply(
            lambda x: "Yes" if pd.to_datetime(x.get(visit_col), errors='coerce').month == next_month else "No",
            axis=1
        )

        # ================= PART DETAILS =================
        parts = ["AF","OF","OIL","AOS","RGT","VK"]

        for part in parts:
            r_col = next((c for c in df.columns if part.lower() in c.lower() and "r date" in c.lower()), None)
            rem_col = next((c for c in df.columns if part.lower() in c.lower() and "rem" in c.lower()), None)

            priority_df[f"{part} R Date"] = priority_df[r_col] if r_col else ""
            priority_df[f"{part} Rem"] = priority_df[rem_col] if rem_col else ""

        # ================= DISPLAY =================
        show_cols = [
            fab_col, cust_col, model_col, loc_col, contact_col, visit_col,
            "Overdue", "Current Month Overdue", "Next Month Overdue",
            "AF R Date","AF Rem","OF R Date","OF Rem",
            "OIL R Date","OIL Rem","AOS R Date","AOS Rem",
            "RGT R Date","RGT Rem","VK R Date","VK Rem"
        ]

        show_cols = [c for c in show_cols if c in priority_df.columns]

        st.dataframe(priority_df[show_cols], use_container_width=True)

    else:
        st.info("No priority visits found")

# ================= CHART =================
status_col = get_col("status")

if status_col:
    st.subheader("📊 Status Chart")
    fig = px.pie(df_f, names=status_col)
    st.plotly_chart(fig, use_container_width=True)
