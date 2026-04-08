import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(layout="wide")

# ================= LOGIN =================
USER_DB = {"admin": "admin123"}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if USER_DB.get(u) == p:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Invalid Login")
    st.stop()

# ================= LOAD =================
df = pd.read_excel("Master_OD_Data.xlsx").fillna("")
df.columns = df.columns.str.strip()

# ================= SAFE COLUMN =================
def get_col(keyword):
    return next((c for c in df.columns if keyword.lower() in c.lower()), None)

cust_col = get_col("customer")
fab_col = get_col("fabrication")
model_col = get_col("model")
loc_col = get_col("location")
contact_col = get_col("contact")
visit_col = get_col("visit")
priority_col = get_col("priority visits")
w_col = get_col("warranty")
amc_col = get_col("amc")

# ================= FILTER =================
df[cust_col] = df[cust_col].astype(str)
customers = ["All"] + sorted(df[cust_col].unique())

sel = st.sidebar.selectbox("Customer", customers)
df_f = df if sel == "All" else df[df[cust_col] == sel]

# ================= EXPORT =================
def to_excel(df):
    buf = BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

# ================= DASHBOARD =================
st.title("🏭 Industrial Dashboard")
st.metric("Total Units", len(df_f))

# ================= SIDEBAR WARRANTY =================
st.sidebar.subheader("📅 Warranty Monthly")

if w_col:
    df[w_col] = pd.to_datetime(df[w_col], errors='coerce')
    df["Warranty End"] = df[w_col] + pd.DateOffset(years=1)

    df_w = df.dropna(subset=["Warranty End"])

    if not df_w.empty:
        year = st.sidebar.selectbox("Year", sorted(df_w["Warranty End"].dt.year.unique()), key="w")

        df_wy = df_w[df_w["Warranty End"].dt.year == year]
        st.sidebar.write(df_wy["Warranty End"].dt.month.value_counts().sort_index())

# ================= SIDEBAR AMC =================
st.sidebar.subheader("📆 AMC Monthly")

if amc_col:
    df[amc_col] = pd.to_datetime(df[amc_col], errors='coerce')

    df_a = df.dropna(subset=[amc_col])

    if not df_a.empty:
        year_a = st.sidebar.selectbox("AMC Year", sorted(df_a[amc_col].dt.year.unique()), key="a")

        df_ay = df_a[df_a[amc_col].dt.year == year_a]
        st.sidebar.write(df_ay[amc_col].dt.month.value_counts().sort_index())

# ================= PRIORITY =================
st.subheader("🚨 Priority Visit Dashboard")

if priority_col:

    p_df = df_f[df_f[priority_col].astype(str).str.strip() != ""]

    if not p_df.empty:

        st.success(f"{len(p_df)} Priority Visits Found")

        # ================= SCORING =================
        def score(row):
            try:
                last = pd.to_datetime(row.get(visit_col), errors='coerce')
                days = (datetime.today() - last).days

                if days > 60:
                    return "🔴 High"
                elif days > 30:
                    return "🟡 Medium"
                else:
                    return "🟢 Normal"
            except:
                return "Unknown"

        p_df["Priority Score"] = p_df.apply(score, axis=1)

        # ================= SAFE COLUMN LIST =================
        show_cols = []

        for c in [fab_col, cust_col, model_col, loc_col,
                  contact_col, visit_col, priority_col, "Priority Score"]:
            if c and c in p_df.columns:
                show_cols.append(c)

        st.dataframe(p_df[show_cols], use_container_width=True)

        # ================= EXPORT =================
        st.download_button("📥 Download Priority Excel", to_excel(p_df))

        # ================= WHATSAPP =================
        st.subheader("📲 WhatsApp Alert")

        if st.button("Send Priority Alerts"):
            st.success("✅ Alerts Sent (Demo Mode)")

    else:
        st.warning("No Priority Visit Data")

# ================= MACHINE =================
st.subheader("🔍 Machine Tracker")

machines = ["Select"] + list(df_f[fab_col].unique())
sel_f = st.selectbox("Machine", machines)

if sel_f != "Select":
    row = df_f[df_f[fab_col] == sel_f].iloc[0]

    st.dataframe(pd.DataFrame([row]))

    st.subheader("🔧 Parts")

    parts = ["AF","OF","OIL","AOS","RGT","VK"]

    for part in parts:
        rem_col = next((c for c in df.columns if part.lower() in c.lower() and "rem" in c.lower()), None)
        due_col = next((c for c in df.columns if part.lower() in c.lower() and "due" in c.lower()), None)

        rem = row.get(rem_col, "N/A")
        due = row.get(due_col, "N/A")

        st.write(f"{part} → Remaining: {rem} | Due: {due}")
