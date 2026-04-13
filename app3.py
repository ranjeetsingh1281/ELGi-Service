import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(layout="wide")

# ================= LOGIN =================
USER_DB = {"admin": "admin123", "viewer": "demo"}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 ELGi Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if USER_DB.get(u) == p:
            st.session_state.login = True
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Invalid Login")
    st.stop()

st.sidebar.title(f"👋 {st.session_state.user}")

# ================= LOAD =================
df = pd.read_excel("Master_OD_Data.xlsx").fillna("")

# CLEAN COLUMN NAMES (IMPORTANT)
df.columns = df.columns.str.strip().str.replace("\n","").str.replace("\r","")

# ================= SAFE COLUMN FIND =================
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

# ================= WARRANTY SIDEBAR =================
st.sidebar.subheader("📅 Warranty Monthly")

if w_col:
    df[w_col] = pd.to_datetime(df[w_col], errors='coerce')
    df["Warranty End"] = df[w_col] + pd.DateOffset(years=1)

    df_w = df.dropna(subset=["Warranty End"])

    if not df_w.empty:
        year = st.sidebar.selectbox("Warranty Year", sorted(df_w["Warranty End"].dt.year.unique()))

        df_wy = df_w[df_w["Warranty End"].dt.year == year]
        st.sidebar.write(df_wy["Warranty End"].dt.month.value_counts().sort_index())

# ================= AMC SIDEBAR =================
st.sidebar.subheader("📆 AMC Monthly")

if amc_col:
    df[amc_col] = pd.to_datetime(df[amc_col], errors='coerce')

    df_a = df.dropna(subset=[amc_col])

    if not df_a.empty:
        year_a = st.sidebar.selectbox("AMC Year", sorted(df_a[amc_col].dt.year.unique()))

        df_ay = df_a[df_a[amc_col].dt.year == year_a]
        st.sidebar.write(df_ay[amc_col].dt.month.value_counts().sort_index())

# ================= PRIORITY =================
st.subheader("🚨 Priority Visit Dashboard")

if priority_col:

    p_df = df_f[df_f[priority_col].astype(str).str.strip() != ""]

    if not p_df.empty:

        st.success(f"{len(p_df)} Priority Visits Found")

        p_df = p_df.copy()

        # ===== SCORING =====
        def score(row):
            try:
                last = pd.to_datetime(row.get(visit_col), errors='coerce')
                if pd.isna(last):
                    return "Unknown"

                days = (datetime.today() - last).days

                if days > 60:
                    return "🔴 High"
                elif days > 30:
                    return "🟡 Medium"
                else:
                    return "🟢 Normal"
            except:
                return "Unknown"

        if visit_col:
            p_df["Priority Score"] = p_df.apply(score, axis=1)

        # ===== SAFE COLUMNS =====
        cols = [fab_col, cust_col, model_col, loc_col,
                contact_col, visit_col, priority_col, "Priority Score"]

        safe_cols = [c for c in cols if c and c in p_df.columns]

        # ===== CRASH PROOF DISPLAY =====
        display_df = p_df[safe_cols].copy()

        for col in display_df.columns:
            display_df[col] = display_df[col].astype(str)

        st.dataframe(display_df, use_container_width=True)

        st.download_button("📥 Download Priority Excel", to_excel(display_df))

        # ===== WHATSAPP =====
        if st.button("📲 Send WhatsApp Alerts"):
            st.success("Alert sent (Demo Mode)")

    else:
        st.warning("No Priority Visit Data")

# ================= MACHINE TRACKER =================
st.subheader("🔍 Machine Tracker")

machines = ["Select"] + list(df_f[fab_col].unique())
sel_f = st.selectbox("Select Machine", machines)

if sel_f != "Select":

    row_df = df_f[df_f[fab_col] == sel_f]

    if not row_df.empty:
        row = row_df.iloc[0]

        st.dataframe(pd.DataFrame([row]))

        st.subheader("🔧 Parts Details")

        parts = ["AF","OF","OIL","AOS","RGT","VK","PF","FF","CF"]

        for part in parts:

            rep_col = next((c for c in df.columns if part.lower() in c.lower() and "r date" in c.lower()), None)
            rem_col = next((c for c in df.columns if part.lower() in c.lower() and "rem" in c.lower()), None)
            due_col = next((c for c in df.columns if part.lower() in c.lower() and "due" in c.lower()), None)

            rep = row.get(rep_col, "N/A")
            rem = row.get(rem_col, "N/A")
            due = row.get(due_col, "N/A")

            color = "🟢"
            try:
                if float(rem) < 200:
                    color = "🔴"
                elif float(rem) < 500:
                    color = "🟡"
            except:
                pass

            overdue = ""
            try:
                if pd.to_datetime(due, errors='coerce') < pd.Timestamp.today():
                    overdue = "⚠️ OVERDUE"
            except:
                pass

            st.write(f"{color} {part} → R: {rep} | Rem: {rem} | Due: {due} {overdue}")
