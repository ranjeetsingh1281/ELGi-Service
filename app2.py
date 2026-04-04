import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib import colors
import openai
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

# ================= COLUMN =================
cust_col = next((c for c in df.columns if "customer" in c.lower()), None)
fab_col = next((c for c in df.columns if "fabrication" in c.lower()), None)
status_col = next((c for c in df.columns if "status" in c.lower()), None)
cat_col = next((c for c in df.columns if "category" in c.lower()), None)

w_col = next((c for c in df.columns if "warranty start" in c.lower()), None)
amc_col = next((c for c in df.columns if "amc" in c.lower()), None)
priority_col = next((c for c in df.columns if "priority" in c.lower()), None)

red_col = next((c for c in df.columns if "red" in c.lower()), None)
yellow_col = next((c for c in df.columns if "yellow" in c.lower()), None)
green_col = next((c for c in df.columns if "green" in c.lower()), None)

# ================= FILTER =================
customers = ["All"] + sorted(df[cust_col].astype(str).unique())
sel = st.sidebar.selectbox("Customer", customers)

df_f = df if sel == "All" else df[df[cust_col] == sel]

# ================= SIDEBAR COUNTS =================
st.sidebar.subheader("📊 Unit Count")
st.sidebar.write(df_f[status_col].value_counts())

if cat_col:
    st.sidebar.subheader("📊 Category Count")
    st.sidebar.write(df_f[cat_col].value_counts())

# ================= DASHBOARD =================
st.title("🏭 Industrial Dashboard")

c1,c2 = st.columns(2)
c1.metric("Total Units", len(df_f))
c2.metric("Active Units", len(df_f[df_f[status_col].str.contains("active", case=False)]))

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

# ================= MACHINE =================
st.subheader("🔍 Machine Tracker")

sel_f = st.selectbox("Fabrication", ["Select"] + list(df_f[fab_col].astype(str).unique()))

if sel_f != "Select":

    row = df_f[df_f[fab_col]==sel_f].iloc[0]
    st.dataframe(pd.DataFrame([row]))

    # FOC
    foc_fab = next((c for c in foc.columns if "fabrication" in c.lower()), None)
    st.subheader("🎁 FOC")
    st.dataframe(foc[foc[foc_fab]==sel_f])

    # SERVICE
    srv_fab = next((c for c in service.columns if "fabrication" in c.lower()), None)
    st.subheader("🛠 Service")
    st.dataframe(service[service[srv_fab]==sel_f])

    # AI Prediction
    st.subheader("🤖 AI Prediction")
    try:
        hmr = float(row.get("HMR",0))
        st.success(f"Next Service ~ {int(hmr+500)} Hrs")
    except:
        st.info("No data")

# ================= AI CHAT =================
openai.api_key = os.getenv("OPENAI_API_KEY","YOUR_API_KEY")

def ask_ai(q):
    return openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":q}]
    ).choices[0].message.content

st.subheader("🤖 AI Chatbot")

q = st.text_input("Ask")

if st.button("Ask AI"):
    st.success(ask_ai(q))

# ================= AI REPORT =================
st.subheader("📊 AI Report")

if st.button("Generate Report"):
    st.success(ask_ai("Generate maintenance summary"))

# ================= VOICE =================
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 बोलो...")
        audio = r.listen(source)
    try:
        return r.recognize_google(audio)
    except:
        return ""

st.subheader("🎤 Voice")

if st.button("Start Voice"):
    cmd = listen()
    st.write(cmd)
    st.success(ask_ai(cmd))