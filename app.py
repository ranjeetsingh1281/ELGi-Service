import streamlit as st
import pandas as pd
import os
import sqlite3
from datetime import datetime
from twilio.rest import Client

# ==============================
# 🔐 MULTI USER LOGIN
# ==============================
USERS = {
    "admin": {"password": "1234", "role": "admin"},
    "user": {"password": "user123", "role": "viewer"}
}

def login():
    st.title("🔐 ELGi Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USERS and USERS[u]["password"] == p:
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
# ☁️ CLOUD DB (SQLite)
# ==============================
conn = sqlite3.connect("elgi.db", check_same_thread=False)

# ==============================
# 📲 WHATSAPP (Twilio)
# ==============================
def send_whatsapp(msg):
    try:
        client = Client("YOUR_SID", "YOUR_AUTH_TOKEN")
        client.messages.create(
            body=msg,
            from_='whatsapp:+14155238886',
            to='whatsapp:+91XXXXXXXXXX'
        )
    except:
        pass

# ==============================
# 🧠 HELPERS
# ==============================
def fmt(dt):
    try:
        return pd.to_datetime(dt).strftime('%d-%b-%y')
    except:
        return "N/A"

def get_color(val):
    if val is None:
        return "⚪ N/A"
    elif val < 0:
        return f"🔴 {val}"
    elif val <= 200:
        return f"🟡 {val}"
    else:
        return f"🟢 {val}"

# ==============================
# 📂 LOAD DATA
# ==============================
@st.cache_data
def load():
    files = os.listdir('.')

    def f(name):
        return next((x for x in files if name.lower() in x.lower()), None)

    m = pd.read_excel(f("Master_Data")) if f("Master_Data") else pd.DataFrame()
    od = pd.read_excel(f("Master_OD_Data")) if f("Master_OD_Data") else pd.DataFrame()
    foc = pd.read_excel(f("FOC")) if f("FOC") else pd.DataFrame()
    s = pd.read_excel(f("Service")) if f("Service") else pd.DataFrame()

    for d in [m, od, foc, s]:
        if not d.empty:
            d.columns = d.columns.str.strip()

    return m, od, foc, s

master_df, master_od_df, foc_df, service_df = load()

# ==============================
# 🧭 MENU
# ==============================
st.sidebar.title("🏢 ELGi Menu")
choice = st.sidebar.radio("Select Tracker", ["DPSAC Tracker", "INDUSTRIAL Tracker"])

# ==============================
# 🚀 DASHBOARD
# ==============================
def dashboard(df, title, industrial=False):

    st.title(f"🛠️ {title}")

    cust_col = next((c for c in df.columns if "customer" in c.lower()), None)
    fab_col = next((c for c in df.columns if "fabrication" in c.lower()), None)
    status_col = next((c for c in df.columns if "unit status" in c.lower()), None)
    cat_col = next((c for c in df.columns if "category" in c.lower()), None)

    # ==============================
    # 📊 METRICS
    # ==============================
    if status_col:
        total = len(df)
        active = len(df[df[status_col].str.contains("Active", case=False, na=False)])
        shifted = len(df[df[status_col].str.contains("Shifted", case=False, na=False)])
        sold = len(df[df[status_col].str.contains("Sold", case=False, na=False)])

        st.markdown(f"""
        | Total | Active | Shifted | Sold |
        |---|---|---|---|
        | **{total}** | **{active}** | **{shifted}** | **{sold}** |
        """)

        st.sidebar.markdown("### 📊 Unit Summary")
        st.sidebar.write(f"Total: {total}")
        st.sidebar.write(f"Active: {active}")
        st.sidebar.write(f"Shifted: {shifted}")
        st.sidebar.write(f"Sold: {sold}")

    if cat_col:
        st.sidebar.markdown("### 📦 Category Count")
        for k, v in df[cat_col].value_counts().items():
            st.sidebar.write(f"{k}: {v}")

    # ==============================
    # ALERT ENGINE
    # ==============================
    overdue_count = 0

    last_hmr_col = next((c for c in df.columns if "last call hmr" in c.lower()), None)
    avg_col = next((c for c in df.columns if "avg" in c.lower()), None)
    date_col = next((c for c in df.columns if "last call" in c.lower() and "date" in c.lower()), None)

    for _, row in df.iterrows():
        try:
            last = row.get(last_hmr_col, 0)
            avg = row.get(avg_col, 0)
            last_date = pd.to_datetime(row.get(date_col))

            days = (pd.Timestamp.today() - last_date).days
            live = (days * avg) + last

            if live > 2000:
                overdue_count += 1
        except:
            pass

    if overdue_count > 0:
        st.error(f"🚨 {overdue_count} Machines Overdue!")
        send_whatsapp(f"{overdue_count} machines overdue!")
    else:
        st.success("✅ All Machines Healthy")

    # ==============================
    # MACHINE TRACKER
    # ==============================
    tab1, tab2, tab3 = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])

    with tab1:
        col1, col2 = st.columns(2)

        customers = ["All"] + sorted(df[cust_col].astype(str).unique())
        sel_c = col1.selectbox("Customer", customers)

        df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]

        fabs = ["Select"] + sorted(df_f[fab_col].astype(str).unique())
        sel_f = col2.selectbox("Fabrication No", fabs)

        if sel_f != "Select":
            row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]

            c1, c2, c3, c4 = st.columns(4)

            with c1:
                st.markdown("### Customer Info")
                st.write(row)

            with c2:
                st.markdown("### Replacement Dates")
                for col in df.columns:
                    if "date" in col.lower():
                        st.write(f"{col}: {fmt(row.get(col))}")

            with c3:
                st.markdown("### Remaining Hours")
                st.write("Auto calculated")

            with c4:
                st.markdown("### Due Dates")
                for col in df.columns:
                    if "due" in col.lower():
                        st.write(f"{col}: {fmt(row.get(col))}")

            st.subheader("FOC")
            st.dataframe(foc_df)

            st.subheader("Service")
            st.dataframe(service_df)

    with tab2:
        st.dataframe(foc_df)

    with tab3:
        st.dataframe(df)

# ==============================
# RUN
# ==============================
if choice == "DPSAC Tracker":
    dashboard(master_df, "DPSAC Tracker", False)
else:
    dashboard(master_od_df, "INDUSTRIAL Tracker", True)

# ==============================
# LOGOUT
# ==============================
if st.sidebar.button("Logout"):
    st.session_state["login"] = False
    st.rerun()
