import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from io import BytesIO
import urllib.parse
import requests

# ==============================
# CONFIG
# ==============================
st.set_page_config(layout="wide")

# ==============================
# DARK UI
# ==============================
st.markdown("""
<style>
body {background-color:#0f172a;color:white;}
</style>
""", unsafe_allow_html=True)

# ==============================
# LOGIN (WITH VIEWER)
# ==============================
USER_DB = {
    "admin": {"pass": "admin123", "role": "admin"},
    "user": {"pass": "123", "role": "user"},
    "viewer": {"pass": "demo", "role": "viewer"}
}

if "login" not in st.session_state:

    st.title("🔐 ELGi Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USER_DB and USER_DB[u]["pass"] == p:
            st.session_state["login"] = True
            st.session_state["role"] = USER_DB[u]["role"]
            st.session_state["user"] = u
            st.rerun()
        else:
            st.error("Invalid Login")

    st.stop()

role = st.session_state["role"]

# ==============================
# HELPERS
# ==============================
def smart_get(row, keys):
    for col in row.index:
        c = str(col).lower().replace(" ","").replace("-","")
        if all(k in c for k in keys):
            return row[col]
    return "N/A"

def fmt(x):
    try: return pd.to_datetime(x).strftime('%d-%b-%y')
    except: return "N/A"

def color(v):
    try:
        v = float(v)
        if v < 0: return f"🔴 {v}"
        elif v <= 200: return f"🟡 {v}"
        else: return f"🟢 {v}"
    except:
        return "N/A"

def to_excel(df):
    buf = BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

# ==============================
# LOAD DATA
# ==============================
master = pd.read_excel("Master_Data.xlsx")
master.columns = master.columns.str.strip()

# ==============================
# COLUMN DETECT
# ==============================
status_col = next((c for c in master.columns if "status" in c.lower()), None)
cat_col = next((c for c in master.columns if "category" in c.lower()), None)
cust_col = next((c for c in master.columns if "customer" in c.lower()), master.columns[0])
fab_col = next((c for c in master.columns if "fabrication" in c.lower()), master.columns[1])
over_col = next((c for c in master.columns if "over" in c.lower()), None)
hmr_col = next((c for c in master.columns if "hmr" in c.lower()), None)

# ==============================
# SIDEBAR FILTERS
# ==============================
st.sidebar.title(f"👋 {st.session_state['user']} ({role})")

customers = ["All"] + sorted(master[cust_col].astype(str).unique())
sel_c = st.sidebar.selectbox("Customer", customers)

df = master if sel_c == "All" else master[master[cust_col] == sel_c]

# ==============================
# DASHBOARD
# ==============================
st.title("📊 ELGi Executive Dashboard")

total = len(df)
active = len(df[df[status_col].str.contains("active", case=False, na=False)])
shifted = len(df[df[status_col].str.contains("shifted", case=False, na=False)])
sold = len(df[df[status_col].str.contains("sold", case=False, na=False)])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total", total)
c2.metric("Active", active)
c3.metric("Shifted", shifted)
c4.metric("Sold", sold)

# CATEGORY CHART
if cat_col:
    st.subheader("📊 Category Distribution")
    st.plotly_chart(px.pie(df, names=cat_col), use_container_width=True)

# STATUS CHART
st.subheader("📊 Status Distribution")
st.plotly_chart(px.bar(df[status_col].value_counts()), use_container_width=True)

# TREND
if hmr_col:
    st.subheader("📈 HMR Trend")
    st.plotly_chart(px.line(df, y=hmr_col), use_container_width=True)

# ==============================
# MACHINE TRACKER
# ==============================
st.subheader("🔍 Machine Tracker")

sel_f = st.selectbox("Fabrication", ["Select"] + sorted(df[fab_col].astype(str).unique()))

if sel_f != "Select":
    row = df[df[fab_col] == sel_f].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
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
            st.write(p.upper(), color(smart_get(row,[p,"rem"])))

    with col4:
        st.markdown("### 🚨 Due")
        for p in parts:
            st.write(p.upper(), fmt(smart_get(row,[p,"due"])))

# ==============================
# EXPORT (ROLE BASED)
# ==============================
st.subheader("📥 Export")

if role != "viewer":
    st.download_button("📊 Download Excel", to_excel(df), "dashboard.xlsx")
else:
    st.info("👁️ Viewer Mode: Export disabled")

# ==============================
# ALERT
# ==============================
st.subheader("📢 Alert")

msg = st.text_area("Message", "Service Due Alert")

if role != "viewer":
    wa = f"https://wa.me/91XXXXXXXXXX?text={urllib.parse.quote(msg)}"
    st.markdown(f"[📱 Send WhatsApp]({wa})")
else:
    st.info("👁️ Viewer Mode: Alert disabled")

# ==============================
# VOICE COMMAND
# ==============================
import speech_recognition as sr

def voice():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 बोलो...")
        audio = r.listen(source)

    try:
        return r.recognize_google(audio)
    except:
        return ""

if st.button("🎤 Voice Command"):
    cmd = voice()
    st.write("You said:", cmd)

    if "status" in cmd.lower():
        st.success(f"Total machines: {len(df)}")

    if "overdue" in cmd.lower():
        st.error(f"{len(df[df[over_col]>0])} overdue machines")

# ==============================
# AI API (OPTIONAL)
# ==============================
st.subheader("🤖 AI Prediction")

if st.button("Run AI"):
    try:
        res = requests.post(
            "http://127.0.0.1:8000/predict",
            json={"hmr":1000,"avg":10}
        )
        st.write(res.json())
    except:
        st.warning("ML API not running")