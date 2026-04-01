import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse

# ==============================
# CONFIG
# ==============================
st.set_page_config(layout="wide")

# ==============================
# LOGIN
# ==============================
USER_DB = {"admin": "admin123", "user": "123"}

if "login" not in st.session_state:
    st.title("🔐 ELGi Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USER_DB and USER_DB[u] == p:
            st.session_state["login"] = True
            st.session_state["user"] = u
            st.rerun()
        else:
            st.error("Invalid Login")
    st.stop()

# ==============================
# HELPERS
# ==============================
def fmt(dt):
    try:
        return pd.to_datetime(dt).strftime('%d-%b-%y')
    except:
        return "N/A"

def color(val):
    try:
        val = float(val)
        if val < 0:
            return f"🔴 {val}"
        elif val <= 200:
            return f"🟡 {val}"
        else:
            return f"🟢 {val}"
    except:
        return "N/A"

def smart_get(row, keys):
    for col in row.index:
        c = str(col).lower().replace(" ", "").replace("-", "")
        if all(k in c for k in keys):
            return row[col]
    return "N/A"

# ==============================
# LOAD DATA
# ==============================
@st.cache_data
def load():
    m = pd.read_excel("Master_Data.xlsx")
    f = pd.read_excel("Active_FOC.xlsx")
    s = pd.read_excel("Service_Details.xlsx")

    for d in [m,f,s]:
        d.columns = d.columns.str.strip()

    return m,f,s

master,foc,service = load()

# ==============================
# SIDEBAR FILTERS
# ==============================
st.sidebar.title("🔍 Filters")

cust_col = next((c for c in master.columns if "customer" in c.lower()), master.columns[0])
date_col = next((c for c in master.columns if "date" in c.lower()), None)

customers = ["All"] + sorted(master[cust_col].astype(str).unique())
sel_c = st.sidebar.selectbox("Customer", customers)

if date_col:
    start = st.sidebar.date_input("From Date", datetime(2023,1,1))
    end = st.sidebar.date_input("To Date", datetime.today())
else:
    start = end = None

# APPLY FILTER
df = master.copy()

if sel_c != "All":
    df = df[df[cust_col] == sel_c]

if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df = df[(df[date_col] >= pd.to_datetime(start)) & (df[date_col] <= pd.to_datetime(end))]

# ==============================
# DASHBOARD
# ==============================
st.title("📊 ELGi Premium Dashboard")

status_col = next((c for c in master.columns if "status" in c.lower()), None)

total = len(df)
active = len(df[df[status_col].str.contains("active", case=False, na=False)])
shifted = len(df[df[status_col].str.contains("shifted", case=False, na=False)])
sold = len(df[df[status_col].str.contains("sold", case=False, na=False)])

c1,c2,c3,c4 = st.columns(4)
c1.metric("Total", total)
c2.metric("Active", active)
c3.metric("Shifted", shifted)
c4.metric("Sold", sold)

# ==============================
# CHARTS
# ==============================
st.subheader("📊 Status Distribution")
st.bar_chart(df[status_col].value_counts())

st.subheader("📈 Trend Chart")
hmr_col = next((c for c in master.columns if "hmr" in c.lower()), None)
if hmr_col:
    st.line_chart(df[hmr_col])

# ==============================
# MACHINE TRACKER
# ==============================
st.subheader("🔍 Machine Tracker")

fab_col = next((c for c in master.columns if "fabrication" in c.lower()), master.columns[1])

sel_f = st.selectbox("Select Fabrication", ["Select"] + sorted(df[fab_col].astype(str).unique()))

if sel_f != "Select":

    row = df[df[fab_col] == sel_f].iloc[0]

    col1,col2,col3,col4 = st.columns(4)

    parts = ["oil","afc","afe","mof","rof","aos","rgt","1500","3000"]

    with col1:
        st.markdown("### 📋 Info")
        st.write(row[cust_col])

    with col2:
        st.markdown("### 🔧 Replacement")
        for p in parts:
            st.write(p.upper(), fmt(smart_get(row,[p,"r"])))

    with col3:
        st.markdown("### ⏳ Remaining")
        for p in parts:
            val = smart_get(row,[p,"rem"])
            st.write(p.upper(), color(val))

    with col4:
        st.markdown("### 🚨 Due")
        for p in parts:
            st.write(p.upper(), fmt(smart_get(row,[p,"due"])))

# ==============================
# OVERDUE PANEL
# ==============================
over_col = next((c for c in master.columns if "over" in c.lower()), None)

if over_col:
    master[over_col] = pd.to_numeric(master[over_col], errors='coerce').fillna(0)
    overdue = master[master[over_col] > 0]

    if len(overdue) > 0:
        st.error(f"🚨 {len(overdue)} Machines Overdue")

# ==============================
# WHATSAPP ALERT
# ==============================
st.subheader("📢 Send Alert")

msg = st.text_area("Message", "Service Due Alert")

wa = f"https://wa.me/917061158953?text={urllib.parse.quote(msg)}"
st.markdown(f"[📱 Send WhatsApp Alert]({wa})")