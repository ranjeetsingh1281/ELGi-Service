import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO
from twilio.rest import Client

# ==============================
# 🔐 ROLE BASED LOGIN
# ==============================
USERS = {
    "user1": {"pass": "123", "role": "dpsac"},
    "user2": {"pass": "123", "role": "dpsac"},
    "user3": {"pass": "123", "role": "dpsac"},
    "user4": {"pass": "123", "role": "industrial"},
    "user5": {"pass": "123", "role": "industrial"},
    "user6": {"pass": "123", "role": "industrial"},
    "admin1": {"pass": "admin", "role": "admin"},
    "admin2": {"pass": "admin", "role": "admin"},
}

def login():
    st.title("🔐 ELGi Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USERS and USERS[u]["pass"] == p:
            st.session_state["login"] = True
            st.session_state["role"] = USERS[u]["role"]
            st.success("Login Success")
            st.rerun()
        else:
            st.error("Invalid Credentials")

if "login" not in st.session_state:
    st.session_state["login"] = False

if not st.session_state["login"]:
    login()
    st.stop()

# ==============================
# ⚙️ CONFIG
# ==============================
st.set_page_config(layout="wide")

# ==============================
# 📲 WHATSAPP ALERT
# ==============================
def send_whatsapp(msg):
    try:
        client = Client("YOUR_SID", "YOUR_TOKEN")
        client.messages.create(
            body=msg,
            from_='whatsapp:+14155238886',
            to='whatsapp:+91XXXXXXXXXX'
        )
    except:
        pass

# ==============================
# 📂 FILE UPLOAD SYSTEM
# ==============================
st.sidebar.markdown("### 📂 Upload Excel")
uploaded = st.sidebar.file_uploader("Upload Master File", type=["xlsx"])

def load_data():
    if uploaded:
        df = pd.read_excel(uploaded)
        df.columns = df.columns.str.strip()
        return df
    else:
        st.warning("Upload Excel File")
        return pd.DataFrame()

df = load_data()

# ==============================
# 📊 HELPERS
# ==============================
def fmt(dt):
    try:
        return pd.to_datetime(dt).strftime('%d-%b-%y')
    except:
        return "N/A"

def to_excel(df):
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    return buffer.getvalue()

# ==============================
# 📊 SIDEBAR ACCESS CONTROL
# ==============================
role = st.session_state["role"]

if role == "dpsac":
    choice = "DPSAC Tracker"
elif role == "industrial":
    choice = "INDUSTRIAL Tracker"
else:
    choice = st.sidebar.radio("Select Tracker", ["DPSAC Tracker", "INDUSTRIAL Tracker"])

# ==============================
# 📊 DASHBOARD
# ==============================
def dashboard(df, title):

    st.title(title)

    if df.empty:
        return

    status_col = next((c for c in df.columns if "status" in c.lower()), None)
    cust_col = next((c for c in df.columns if "customer" in c.lower()), None)
    fab_col = next((c for c in df.columns if "fabrication" in c.lower()), None)

    # METRICS
    if status_col:
        total = len(df)
        active = len(df[df[status_col].str.contains("Active", case=False, na=False)])
        shifted = len(df[df[status_col].str.contains("Shifted", case=False, na=False)])
        sold = len(df[df[status_col].str.contains("Sold", case=False, na=False)])

        st.metric("Total", total)
        st.metric("Active", active)
        st.metric("Shifted", shifted)
        st.metric("Sold", sold)

        st.sidebar.markdown("### 📊 Summary")
        st.sidebar.write(f"Total: {total}")
        st.sidebar.write(f"Active: {active}")
        st.sidebar.write(f"Shifted: {shifted}")
        st.sidebar.write(f"Sold: {sold}")

    # ALERT ENGINE
    overdue = 0
    for _, row in df.iterrows():
        try:
            if row.get("HMR Cal.", 0) > 2000:
                overdue += 1
        except:
            pass

    if overdue > 0:
        st.error(f"🚨 {overdue} Machines Overdue!")
        send_whatsapp(f"{overdue} machines overdue!")
    else:
        st.success("All Good")

    # FILTER
    customers = ["All"] + sorted(df[cust_col].astype(str).unique())
    sel_c = st.selectbox("Customer", customers)

    df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]

    fabs = ["Select"] + sorted(df_f[fab_col].astype(str).unique())
    sel_f = st.selectbox("Fabrication No", fabs)

    if sel_f != "Select":
        row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]

        st.subheader("Machine Details")
        st.write(row)

    # REPORT
    st.download_button("📥 Download Report", to_excel(df), "report.xlsx")

# ==============================
# RUN
# ==============================
if choice == "DPSAC Tracker":
    dashboard(df, "DPSAC Tracker")
else:
    dashboard(df, "Industrial Tracker")

# ==============================
# LOGOUT
# ==============================
if st.sidebar.button("Logout"):
    st.session_state["login"] = False
    st.rerun()
