import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib import colors

st.set_page_config(layout="wide")

# ==============================
# 🔐 SECURE LOGIN (NO BYPASS)
# ==============================
USER_DB = {
    "admin": {"pass": "admin123", "role": "admin"},
    "user": {"pass": "123", "role": "user"},
    "viewer": {"pass": "demo", "role": "viewer"}
}

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:

    st.title("🔐 Industrial Tracker Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USER_DB and USER_DB[u]["pass"] == p:
            st.session_state["login"] = True
            st.session_state["user"] = u
            st.session_state["role"] = USER_DB[u]["role"]
            st.rerun()
        else:
            st.error("❌ Invalid Username or Password")

    st.stop()

# ==============================
# SESSION SAFE
# ==============================
user = st.session_state.get("user", "Guest")
role = st.session_state.get("role", "viewer")

# ==============================
# LOGOUT
# ==============================
if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.rerun()

st.sidebar.title(f"👋 {user} ({role})")

# ==============================
# EXPORT FUNCTIONS
# ==============================
def to_excel(df):
    buf = BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

def to_pdf(df):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf)

    data = [df.columns.tolist()] + df.astype(str).values.tolist()

    table = Table(data)
    table.setStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.grey),
        ('GRID',(0,0),(-1,-1),1,colors.black)
    ])

    doc.build([table])
    return buf.getvalue()

# ==============================
# LOAD DATA (SAFE)
# ==============================
try:
    df = pd.read_excel("Master_OD_Data.xlsx")
    foc = pd.read_excel("Active_FOC.xlsx")
except:
    st.error("❌ Excel file not found")
    st.stop()

df.columns = df.columns.str.strip()
foc.columns = foc.columns.str.strip()

df = df.fillna("")

# ==============================
# COLUMN DETECT (SAFE)
# ==============================
cust_col = next((c for c in df.columns if "customer" in c.lower()), None)
fab_col = next((c for c in df.columns if "fabrication" in c.lower()), None)
status_col = next((c for c in df.columns if "status" in c.lower()), None)

if cust_col is None:
    st.error("❌ Customer column not found")
    st.stop()

# ==============================
# FILTER
# ==============================
try:
    customers = ["All"] + sorted(df[cust_col].dropna().astype(str).unique().tolist())
except:
    customers = ["All"]

sel = st.sidebar.selectbox("Customer", customers)

df_f = df if sel == "All" else df[df[cust_col].astype(str) == sel]

# ==============================
# DASHBOARD
# ==============================
st.title("🏭 Industrial Dashboard")

total = len(df_f)

active = 0
if status_col:
    active = len(df_f[df_f[status_col].astype(str).str.contains("active", case=False)])

c1, c2 = st.columns(2)
c1.metric("Total Units", total)
c2.metric("Active Units", active)

# ==============================
# HEALTH COUNT
# ==============================
st.subheader("🚦 Health Status")

red_col = next((c for c in df.columns if "red" in c.lower()), None)
yellow_col = next((c for c in df.columns if "yellow" in c.lower()), None)
green_col = next((c for c in df.columns if "green" in c.lower()), None)

c1, c2, c3 = st.columns(3)

c1.metric("🔴 Red", int(pd.to_numeric(df_f.get(red_col, 0), errors='coerce').sum()))
c2.metric("🟡 Yellow", int(pd.to_numeric(df_f.get(yellow_col, 0), errors='coerce').sum()))
c3.metric("🟢 Green", int(pd.to_numeric(df_f.get(green_col, 0), errors='coerce').sum()))

# ==============================
# WARRANTY EXPIRED
# ==============================
w_col = next((c for c in df.columns if "warranty start" in c.lower()), None)

if w_col:
    df_f[w_col] = pd.to_datetime(df_f[w_col], errors='coerce')
    df_f["Warranty End"] = df_f[w_col] + pd.DateOffset(years=1)

    expired = df_f[df_f["Warranty End"] < datetime.today()]

    st.subheader("📅 Warranty Expired")
    st.dataframe(expired, use_container_width=True)

# ==============================
# AMC EXPIRED
# ==============================
amc_col = next((c for c in df.columns if "amc" in c.lower()), None)

if amc_col:
    st.subheader("📆 AMC Expired")
    st.dataframe(df_f[[cust_col, fab_col, amc_col]], use_container_width=True)

# ==============================
# PRIORITY VISITS
# ==============================
priority_col = next((c for c in df.columns if "priority" in c.lower()), None)

if priority_col:
    st.subheader("🚨 Priority Visits")
    st.dataframe(df_f[df_f[priority_col] != ""], use_container_width=True)

# ==============================
# MACHINE TRACKER
# ==============================
st.subheader("🔍 Machine Tracker")

if fab_col:
    sel_f = st.selectbox("Fabrication", ["Select"] + list(df_f[fab_col].astype(str).unique()))

    if sel_f != "Select":
        st.dataframe(df_f[df_f[fab_col].astype(str) == sel_f])

# ==============================
# FOC LIST
# ==============================
st.subheader("🎁 FOC List")
st.dataframe(foc, use_container_width=True)

# ==============================
# OVERDUE SERVICE
# ==============================
over_col = next((c for c in df.columns if "over" in c.lower()), None)

if over_col:
    df[over_col] = pd.to_numeric(df[over_col], errors='coerce').fillna(0)
    overdue = df[df[over_col] > 0]

    st.subheader("⏳ Overdue Service")
    st.dataframe(overdue, use_container_width=True)

# ==============================
# EXPORT
# ==============================
st.subheader("📥 Export")

if role != "viewer":
    st.download_button("📊 Download Excel", to_excel(df_f), "industrial.xlsx")
    st.download_button("📄 Download PDF", to_pdf(df_f), "industrial.pdf")
else:
    st.info("👁️ Viewer Mode: Export disabled")