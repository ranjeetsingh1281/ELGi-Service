import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib import colors

st.set_page_config(layout="wide")

# ==============================
# LOGIN SYSTEM (FIXED)
# ==============================
USER_DB = {
    "admin": {"pass": "admin123", "role": "admin"},
    "viewer": {"pass": "demo", "role": "viewer"}
}

if "login" not in st.session_state:

    st.title("🔐 Industrial Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USER_DB and USER_DB[u]["pass"] == p:

            st.session_state["login"] = True
            st.session_state["role"] = USER_DB[u]["role"]
            st.session_state["user"] = u   # ✅ FIX

            st.rerun()
        else:
            st.error("Invalid Login")

    st.stop()

# ==============================
# SAFE SESSION (NO ERROR)
# ==============================
user = st.session_state.get("user", "Guest")
role = st.session_state.get("role", "viewer")

# ==============================
# EXPORT
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
# LOAD DATA
# ==============================
df = pd.read_excel("Master_OD_Data.xlsx")
foc = pd.read_excel("Active_FOC.xlsx")

df.columns = df.columns.str.strip()
foc.columns = foc.columns.str.strip()

# ==============================
# COLUMN DETECT
# ==============================
cust_col = next((c for c in df.columns if "customer" in c.lower()), df.columns[0])
fab_col = next((c for c in df.columns if "fabrication" in c.lower()), df.columns[1])
status_col = next((c for c in df.columns if "status" in c.lower()), None)

red_col = next((c for c in df.columns if "red" in c.lower()), None)
yellow_col = next((c for c in df.columns if "yellow" in c.lower()), None)
green_col = next((c for c in df.columns if "green" in c.lower()), None)

w_col = next((c for c in df.columns if "warranty start" in c.lower()), None)
amc_col = next((c for c in df.columns if "amc" in c.lower()), None)
priority_col = next((c for c in df.columns if "priority" in c.lower()), None)
over_col = next((c for c in df.columns if "over" in c.lower()), None)

# ==============================
# SIDEBAR
# ==============================
st.sidebar.title(f"👋 {user} ({role})")

customers = ["All"] + sorted(df[cust_col].astype(str).unique())
sel = st.sidebar.selectbox("Customer", customers)

df_f = df if sel == "All" else df[df[cust_col] == sel]

# ==============================
# DASHBOARD
# ==============================
st.title("🏭 Industrial Dashboard")

total = len(df_f)
active = len(df_f[df_f[status_col].str.contains("active", case=False, na=False)]) if status_col else 0

c1, c2 = st.columns(2)
c1.metric("Total Units", total)
c2.metric("Active Units", active)

# ==============================
# HEALTH COUNT
# ==============================
st.subheader("🚦 Health Status")

c1, c2, c3 = st.columns(3)
c1.metric("🔴 Red", int(df_f[red_col].sum()) if red_col else 0)
c2.metric("🟡 Yellow", int(df_f[yellow_col].sum()) if yellow_col else 0)
c3.metric("🟢 Green", int(df_f[green_col].sum()) if green_col else 0)

# ==============================
# WARRANTY
# ==============================
if w_col:
    df_f[w_col] = pd.to_datetime(df_f[w_col], errors='coerce')
    df_f["Warranty End"] = df_f[w_col] + pd.DateOffset(years=1)

    expired = df_f[df_f["Warranty End"] < datetime.today()]

    st.subheader("📅 Warranty Expired")
    st.dataframe(expired)

# ==============================
# AMC
# ==============================
if amc_col:
    st.subheader("📆 AMC Expired")
    st.dataframe(df_f[[cust_col, fab_col, amc_col]])

# ==============================
# PRIORITY
# ==============================
if priority_col:
    st.subheader("🚨 Priority Visits")
    st.dataframe(df_f[df_f[priority_col].notna()])

# ==============================
# MACHINE TRACKER
# ==============================
st.subheader("🔍 Machine Tracker")

sel_f = st.selectbox("Fabrication", ["Select"] + list(df_f[fab_col].astype(str).unique()))

if sel_f != "Select":
    st.dataframe(df_f[df_f[fab_col] == sel_f])

# ==============================
# FOC
# ==============================
st.subheader("🎁 FOC List")
st.dataframe(foc)

# ==============================
# OVERDUE
# ==============================
if over_col:
    df[over_col] = pd.to_numeric(df[over_col], errors='coerce').fillna(0)
    overdue = df[df[over_col] > 0]

    st.subheader("⏳ Overdue")
    st.dataframe(overdue)

# ==============================
# EXPORT
# ==============================
if role != "viewer":
    st.download_button("📊 Excel", to_excel(df_f), "industrial.xlsx")
    st.download_button("📄 PDF", to_pdf(df_f), "industrial.pdf")
else:
    st.info("Viewer Mode: Export disabled")
