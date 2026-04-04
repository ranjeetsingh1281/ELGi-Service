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

# ==============================
# 🔐 LOGIN (SECURE)
# ==============================
USER_DB = {
    "admin": {"pass": "admin123", "role": "admin"},
    "user": {"pass": "123", "role": "user"},
    "viewer": {"pass": "demo", "role": "viewer"}
}

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    st.title("🔐 ELGi Industrial Login")

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

user = st.session_state.get("user")
role = st.session_state.get("role")

if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.rerun()

st.sidebar.title(f"👋 {user} ({role})")

#===============================
#AI REPORT FUNCTION 
#===============================
openai.api_key = os.getenv("OPENAI_API_KEY","YOUR_API_KEY")

def ask_ai(question, df):

    sample = df.head(20).to_string()

    prompt = f"""
    You are an industrial maintenance assistant.

    Data:
    {sample}

    Question:
    {question}

    Give clear answer.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    except Exception as e:
        return str(e)

# ==============================
# 📥 EXPORT FUNCTIONS
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
# 📂 LOAD DATA
# ==============================
df = pd.read_excel("Master_OD_Data.xlsx").fillna("")
foc = pd.read_excel("Active_FOC.xlsx").fillna("")
service = pd.read_excel("Service_Details.xlsx").fillna("")

df.columns = df.columns.str.strip()
foc.columns = foc.columns.str.strip()
service.columns = service.columns.str.strip()

# ==============================
# 🔎 COLUMN DETECT
# ==============================
cust_col = next((c for c in df.columns if "customer" in c.lower()), None)
fab_col = next((c for c in df.columns if "fabrication" in c.lower()), None)
status_col = next((c for c in df.columns if "status" in c.lower()), None)

w_col = next((c for c in df.columns if "warranty start" in c.lower()), None)
amc_col = next((c for c in df.columns if "amc" in c.lower()), None)
priority_col = next((c for c in df.columns if "priority" in c.lower()), None)

red_col = next((c for c in df.columns if "red" in c.lower()), None)
yellow_col = next((c for c in df.columns if "yellow" in c.lower()), None)
green_col = next((c for c in df.columns if "green" in c.lower()), None)

# ==============================
# 🎯 FILTER
# ==============================
customers = ["All"] + sorted(df[cust_col].astype(str).unique())
sel = st.sidebar.selectbox("Customer", customers)

df_f = df if sel == "All" else df[df[cust_col] == sel]

# ==============================
# 📊 DASHBOARD
# ==============================
st.title("🏭 Industrial Dashboard")

c1, c2 = st.columns(2)
c1.metric("Total Units", len(df_f))
c2.metric("Active Units", len(df_f[df_f[status_col].str.contains("active", case=False)]) if status_col else 0)

#===============================
# 📊 AI REPORT FUNCTION 
#===============================

st.subheader("📊 AI Smart Report")

if st.button("Generate AI Report"):

    report = generate_report(df_f)

    st.success("Report Generated")
    st.write(report)

    st.download_button(
        "Download Report",
        report,
        file_name="AI_Report.txt"
    )


#===============================
#🎤 VOICE DASHBOARD IU
#===============================

st.subheader("🎤 Voice Control")

if st.button("Start Voice Command"):

    cmd = listen_voice()

    st.write("You said:", cmd)

    result = voice_actions(cmd, df_f)

    if isinstance(result, str):
        st.success(result)
    else:
        st.dataframe(result)
# ==============================
# 🚦 HEALTH
# ==============================
st.subheader("🚦 Health Status")

c1,c2,c3 = st.columns(3)
c1.metric("🔴 Red", int(pd.to_numeric(df_f.get(red_col,0), errors='coerce').sum()))
c2.metric("🟡 Yellow", int(pd.to_numeric(df_f.get(yellow_col,0), errors='coerce').sum()))
c3.metric("🟢 Green", int(pd.to_numeric(df_f.get(green_col,0), errors='coerce').sum()))

# ==============================
# 📅 WARRANTY MONTHLY
# ==============================
st.sidebar.subheader("📅 Warranty Monthly")

year = st.sidebar.selectbox("Warranty Year", [2023,2024,2025,2026])

if w_col:
    df_f[w_col] = pd.to_datetime(df_f[w_col], errors='coerce')
    df_f["Warranty End"] = df_f[w_col] + pd.DateOffset(years=1)

    df_w = df_f[df_f["Warranty End"].dt.year == year]

    monthly = df_w["Warranty End"].dt.month.value_counts().sort_index()
    st.sidebar.write(monthly)

    if role != "viewer":
        st.sidebar.download_button("Warranty Excel", to_excel(df_w))
        st.sidebar.download_button("Warranty PDF", to_pdf(df_w))

# ==============================
# 📆 AMC MONTHLY
# ==============================
st.sidebar.subheader("📆 AMC Expired")

if amc_col:
    df_f[amc_col] = pd.to_datetime(df_f[amc_col], errors='coerce')

    df_amc = df_f[df_f[amc_col] < datetime.today()]
    df_amc = df_amc[df_amc[amc_col].dt.year == year]

    monthly = df_amc[amc_col].dt.month.value_counts().sort_index()
    st.sidebar.write(monthly)

    if role != "viewer":
        st.sidebar.download_button("AMC Excel", to_excel(df_amc))
        st.sidebar.download_button("AMC PDF", to_pdf(df_amc))

# ==============================
# 🔍 MACHINE TRACKER
# ==============================
st.subheader("🔍 Machine Tracker")

sel_f = st.selectbox("Fabrication", ["Select"] + list(df_f[fab_col].astype(str).unique()))

if sel_f != "Select":

    row = df_f[df_f[fab_col] == sel_f].iloc[0]

    st.dataframe(pd.DataFrame([row]))

    # ==========================
    # 🎁 FOC (Selected Machine)
    # ==========================
    foc_fab = next((c for c in foc.columns if "fabrication" in c.lower()), None)

    foc_cols = ["Created on","FOC No","Part No","Description","FOC Status","ELGi Invoice No"]

    st.subheader("🎁 FOC List")
    st.dataframe(foc[foc[foc_fab]==sel_f][[c for c in foc_cols if c in foc.columns]])

    # ==========================
    # 🛠 SERVICE
    # ==========================
    srv_fab = next((c for c in service.columns if "fabrication" in c.lower()), None)

    srv_cols = ["Created on","Call No","HMR","Call Type","Service Engineer Comments"]

    st.subheader("🛠 Service History")
    st.dataframe(service[service[srv_fab]==sel_f][[c for c in srv_cols if c in service.columns]])

    # ==========================
    # 🤖 AI
    # ==========================
    st.subheader("🤖 AI Prediction")

    try:
        hmr = float(row.get("HMR",0))
        pred = hmr + 500
        st.success(f"Next Service ~ {int(pred)} Hrs")
    except:
        st.info("Not enough data")

#================================
# 🤖 AI
#================================
st.subheader("🤖 AI Chatboat")

q = st.text_input("Ask anything...")

if st.button("Ask"):
     ans = Chatboat(q, df)
     st.success(ans)

#=================================
# VOICE FUNCTION 
#=================================

def listen_voice():
    r = sr.Recognizer()

    with sr.Microphone() as source:
        st.info("🎤 बोलो Boss...")
        audio = r.listen(source)

    try:
        return r.recognize_google(audio, language="en-IN").lower()
    except:
        return ""


def voice_actions(cmd, df):

    if "report" in cmd:
        return generate_report(df)

    if "overdue" in cmd:
        col = next((c for c in df.columns if "over" in c.lower()), None)
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df[df[col] > 0]

    if "priority" in cmd:
        col = next((c for c in df.columns if "priority" in c.lower()), None)
        return df[df[col].astype(str).str.contains("high", case=False)]

    return "Command not recognized"