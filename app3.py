import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from twilio.rest import Client

# ==============================
# CONFIG
# ==============================
st.set_page_config(layout="wide")

# ==============================
# DARK GLASS UI
# ==============================
st.markdown("""
<style>
body {
    background-color: #0f172a;
    color: white;
}
.glass {
    background: rgba(255,255,255,0.05);
    padding: 15px;
    border-radius: 12px;
    backdrop-filter: blur(10px);
}
</style>
""", unsafe_allow_html=True)

# ==============================
# LOGIN
# ==============================
USER_DB = {"admin":"admin123","user":"123"}

if "login" not in st.session_state:
    st.title("🔐 ELGi Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USER_DB and USER_DB[u] == p:
            st.session_state["login"] = True
            st.rerun()
        else:
            st.error("Invalid Login")
    st.stop()

# ==============================
# HELPERS
# ==============================
def fmt(dt):
    try: return pd.to_datetime(dt).strftime('%d-%b-%y')
    except: return "N/A"

def color(val):
    try:
        val=float(val)
        if val<0: return f"🔴 {val}"
        elif val<=200: return f"🟡 {val}"
        else: return f"🟢 {val}"
    except: return "N/A"

def smart_get(row, keys):
    for col in row.index:
        c=str(col).lower().replace(" ","").replace("-","")
        if all(k in c for k in keys):
            return row[col]
    return "N/A"

# ==============================
# LOAD DATA
# ==============================
master = pd.read_excel("Master_Data.xlsx")
master.columns = master.columns.str.strip()

# ==============================
# FILTERS
# ==============================
st.sidebar.title("🔍 Filters")

cust_col = next((c for c in master.columns if "customer" in c.lower()), master.columns[0])
status_col = next((c for c in master.columns if "status" in c.lower()), None)

sel_c = st.sidebar.selectbox("Customer", ["All"] + sorted(master[cust_col].astype(str).unique()))

df = master if sel_c=="All" else master[master[cust_col]==sel_c]

# ==============================
# KPI CARDS
# ==============================
st.title("📊 ELGi Premium Dashboard")

total=len(df)
active=len(df[df[status_col].str.contains("active",case=False,na=False)])
shifted=len(df[df[status_col].str.contains("shifted",case=False,na=False)])
sold=len(df[df[status_col].str.contains("sold",case=False,na=False)])

c1,c2,c3,c4=st.columns(4)
c1.metric("Total",total)
c2.metric("Active",active)
c3.metric("Shifted",shifted)
c4.metric("Sold",sold)

# ==============================
# PLOTLY CHARTS
# ==============================
st.subheader("📊 Status Distribution")

fig1 = px.pie(df, names=status_col, title="Machine Status")
st.plotly_chart(fig1, use_container_width=True)

hmr_col = next((c for c in master.columns if "hmr" in c.lower()), None)

if hmr_col:
    st.subheader("📈 HMR Trend")
    fig2 = px.line(df, y=hmr_col, title="HMR Trend")
    st.plotly_chart(fig2, use_container_width=True)

# ==============================
# MACHINE TRACKER
# ==============================
st.subheader("🔍 Machine Tracker")

fab_col = next((c for c in master.columns if "fabrication" in c.lower()), master.columns[1])

sel_f = st.selectbox("Fabrication", ["Select"] + sorted(df[fab_col].astype(str).unique()))

if sel_f != "Select":

    row = df[df[fab_col]==sel_f].iloc[0]

    col1,col2,col3,col4 = st.columns(4)

    parts=["oil","afc","afe","mof","rof","aos","rgt","1500","3000"]

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
            st.write(p.upper(), color(smart_get(row,[p,"rem"])))

    with col4:
        st.markdown("### 🚨 Due")
        for p in parts:
            st.write(p.upper(), fmt(smart_get(row,[p,"due"])))

# ==============================
# AUTO ALERT (TWILIO)
# ==============================
def send_whatsapp(msg):
    try:
        client = Client("YOUR_SID","YOUR_TOKEN")
        client.messages.create(
            body=msg,
            from_='whatsapp:+14155238886',
            to='whatsapp:+91XXXXXXXXXX'
        )
    except:
        pass

over_col = next((c for c in master.columns if "over" in c.lower()), None)

if over_col:
    master[over_col] = pd.to_numeric(master[over_col], errors='coerce').fillna(0)
    overdue = master[master[over_col] > 0]

    if len(overdue) > 0:
        st.error(f"🚨 {len(overdue)} Machines Overdue!")
        send_whatsapp(f"{len(overdue)} machines overdue!")
