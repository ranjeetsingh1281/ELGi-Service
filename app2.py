import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib import colors
import speech_recognition as sr
import os

st.set_page_config(layout="wide")

# ================= LOGIN =================
USER_DB = {
    "admin": {"pass": "admin123", "role": "admin"},
    "viewer": {"pass": "demo", "role": "viewer"}
}

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    st.title("🔐 Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USER_DB and USER_DB[u]["pass"] == p:
            st.session_state["login"] = True
            st.session_state["user"] = u
            st.session_state["role"] = USER_DB[u]["role"]
            st.rerun()
        else:
            st.error("Invalid Login")
    st.stop()

user = st.session_state["user"]
role = st.session_state["role"]

st.sidebar.title(f"👋 {user} ({role})")

# ================= LOAD =================
df = pd.read_excel("Master_OD_Data.xlsx").fillna("")
foc = pd.read_excel("Active_FOC.xlsx").fillna("")
service = pd.read_excel("Service_Details.xlsx").fillna("")

df.columns = df.columns.str.strip()
foc.columns = foc.columns.str.strip()
service.columns = service.columns.str.strip()

# ================= COLUMN =================
cust_col = next((c for c in df.columns if "customer" in c.lower()), None)
fab_col = next((c for c in df.columns if "fabrication" in c.lower()), None)
status_col = next((c for c in df.columns if "status" in c.lower()), None)
cat_col = next((c for c in df.columns if "category" in c.lower()), None)

w_col = next((c for c in df.columns if "warranty start" in c.lower()), None)
amc_col = next((c for c in df.columns if "amc" in c.lower()), None)

red_col = next((c for c in df.columns if "red" in c.lower()), None)
yellow_col = next((c for c in df.columns if "yellow" in c.lower()), None)
green_col = next((c for c in df.columns if "green" in c.lower()), None)

# ================= FILTER =================
customers = ["All"] + sorted(df[cust_col].astype(str).unique())
sel = st.sidebar.selectbox("Customer", customers)

df_f = df if sel == "All" else df[df[cust_col].astype(str) == sel]

# ================= SIDEBAR =================
st.sidebar.subheader("📊 Unit Count")
if status_col:
    st.sidebar.write(df_f[status_col].value_counts())

if cat_col:
    st.sidebar.subheader("📊 Category Count")
    st.sidebar.write(df_f[cat_col].value_counts())

# ================= DASHBOARD =================
st.title("🏭 Industrial Dashboard")

c1,c2 = st.columns(2)
c1.metric("Total Units", len(df_f))
c2.metric("Active Units", len(df_f[df_f[status_col].astype(str).str.contains("active", case=False)]) if status_col else 0)

# ================= HEALTH =================
st.subheader("🚦 Health")

c1,c2,c3 = st.columns(3)
c1.metric("🔴 Red", int(pd.to_numeric(df_f.get(red_col,0), errors='coerce').sum()))
c2.metric("🟡 Yellow", int(pd.to_numeric(df_f.get(yellow_col,0), errors='coerce').sum()))
c3.metric("🟢 Green", int(pd.to_numeric(df_f.get(green_col,0), errors='coerce').sum()))

# ================= WARRANTY =================
st.sidebar.subheader("📅 Warranty Monthly")
year = st.sidebar.selectbox("Year", [2023,2024,2025,2026])

if w_col:
    df_f[w_col] = pd.to_datetime(df_f[w_col], errors='coerce')
    df_f["Warranty End"] = df_f[w_col] + pd.DateOffset(years=1)
    df_w = df_f[df_f["Warranty End"].dt.year == year]
    st.sidebar.write(df_w["Warranty End"].dt.month.value_counts().sort_index())

# ================= AMC =================
st.sidebar.subheader("📆 AMC Expired")

if amc_col:
    df_f[amc_col] = pd.to_datetime(df_f[amc_col], errors='coerce')
    df_amc = df_f[df_f[amc_col] < datetime.today()]
    st.sidebar.write(df_amc[amc_col].dt.month.value_counts().sort_index())

# ================= MACHINE TRACKER =================
st.subheader("🔍 Machine Tracker")

df_f[fab_col] = df_f[fab_col].astype(str)

sel_f = st.selectbox("Fabrication", ["Select"] + list(df_f[fab_col].unique()))

if sel_f != "Select":

    filtered = df_f[df_f[fab_col] == sel_f]

    if not filtered.empty:

        row = filtered.iloc[0]
        st.dataframe(pd.DataFrame([row]))

        # FOC
        foc_fab = next((c for c in foc.columns if "fabrication" in c.lower()), None)

        if foc_fab:
            foc_filtered = foc[foc[foc_fab].astype(str) == sel_f]

            foc_cols = ["Created on","FOC No","Part No","Description","FOC Status","ELGi Invoice No"]

            st.subheader("🎁 FOC List")
            st.dataframe(foc_filtered[[c for c in foc_cols if c in foc.columns]])

        # SERVICE
        srv_fab = next((c for c in service.columns if "fabrication" in c.lower()), None)

        if srv_fab:
            srv_filtered = service[service[srv_fab].astype(str) == sel_f]

            srv_cols = ["Created on","Call No","HMR","Call Type","Service Engineer Comments"]

            st.subheader("🛠 Service History")
            st.dataframe(srv_filtered[[c for c in srv_cols if c in service.columns]])

        # AI Prediction
        st.subheader("🤖 AI Prediction")

        try:
            hmr = float(row.get("HMR",0))
            st.success(f"Next Service ~ {int(hmr+500)} Hrs")
        except:
            st.info("No data")

    else:
        st.warning("No data found")

# ================= AI REPORT =================
def generate_report(df):
    return f"""
Total Machines: {len(df)}
Active Machines: {len(df[df[status_col].astype(str).str.contains('active', case=False)]) if status_col else 0}
"""

st.subheader("📊 AI Report")

if st.button("Generate Report"):
    st.success(generate_report(df_f))

# ================= AI CHAT =================
st.subheader("🤖 AI Chatbot")

q = st.text_input("Ask something")

if st.button("Ask AI"):
    st.success(f"Answer: {q}")

# ================= VOICE =================
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Speak...")
        audio = r.listen(source)
    try:
        return r.recognize_google(audio)
    except:
        return ""

st.subheader("🎤 Voice")

if st.button("Start Voice"):
    cmd = listen()
    st.write(cmd)