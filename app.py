import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ==============================
# ⚙️ CONFIG
# ==============================
st.set_page_config(layout="wide")
API = "https://your-api.onrender.com"

# ==============================
# 🔐 LOGIN
# ==============================
st.title("🔐 ELGi Login")

user = st.text_input("Username")
pwd = st.text_input("Password", type="password")

if st.button("Login"):
    res = requests.post(f"{API}/login", params={
        "username": user,
        "password": pwd
    })

    if res.status_code == 200:
        st.session_state["token"] = res.json()["token"]
        st.success("Login Success")
    else:
        st.error("Invalid Login")

# ==============================
# 🧠 HELPER
# ==============================
def fmt(dt):
    try:
        return pd.to_datetime(dt).strftime("%d-%b-%y")
    except:
        return "N/A"

def color(val):
    if val is None:
        return "⚪ N/A"
    elif val < 0:
        return f"🔴 {val}"
    elif val <= 200:
        return f"🟡 {val}"
    else:
        return f"🟢 {val}"

# ==============================
# 📊 DASHBOARD
# ==============================
if "token" in st.session_state:

    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    res = requests.get(f"{API}/machines", headers=headers)

    if res.status_code != 200:
        st.error("API Error")
        st.stop()

    data = res.json()["data"]

    # Convert to DataFrame
    df = pd.DataFrame(data, columns=[
        "id","customer","fabrication","status",
        "hmr","avg_run","last_date"
    ])

    st.title("📊 ELGi Dashboard")

    # ==============================
    # 📊 METRICS
    # ==============================
    total = len(df)
    active = len(df[df["status"]=="Active"])
    shifted = len(df[df["status"]=="Shifted"])
    sold = len(df[df["status"]=="Sold"])

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total", total)
    c2.metric("Active", active)
    c3.metric("Shifted", shifted)
    c4.metric("Sold", sold)

    # ==============================
    # 🚨 ALERT ENGINE
    # ==============================
    overdue = 0
    today = datetime.today()

    for _, r in df.iterrows():
        try:
            days = (today - pd.to_datetime(r["last_date"])).days
            live = (days * r["avg_run"]) + r["hmr"]

            if live > 2000:
                overdue += 1
        except:
            pass

    if overdue > 0:
        st.error(f"🚨 {overdue} Machines Overdue!")
    else:
        st.success("✅ All Machines Healthy")

    # ==============================
    # 🔍 FILTER
    # ==============================
    col1, col2 = st.columns(2)

    customers = ["All"] + sorted(df["customer"].astype(str).unique())
    sel_c = col1.selectbox("Customer", customers)

    df_f = df if sel_c=="All" else df[df["customer"]==sel_c]

    fabs = ["Select"] + sorted(df_f["fabrication"].astype(str).unique())
    sel_f = col2.selectbox("Fabrication No", fabs)

    # ==============================
    # 📋 MACHINE VIEW
    # ==============================
    if sel_f != "Select":

        row = df_f[df_f["fabrication"]==sel_f].iloc[0]

        c1,c2,c3,c4 = st.columns(4)

        # COLUMN 1
        with c1:
            st.markdown("### 📋 Customer Info")
            st.write(f"**Customer:** {row['customer']}")
            st.write(f"**Status:** {row['status']}")
            st.write(f"**Running HMR:** {row['hmr']}")

        # COLUMN 2
        with c2:
            st.markdown("### 🔧 Replacement")
            st.write("From DB / Future mapping")

        # COLUMN 3 (LIVE ENGINE)
        with c3:
            st.markdown("### ⚙️ Remaining Hours")

            try:
                days = (today - pd.to_datetime(row["last_date"])).days
                live = (days * row["avg_run"]) + row["hmr"]

                remaining = 2000 - live

                st.write(f"**Live HMR:** {int(live)}")
                st.write(f"**Remaining:** {color(int(remaining))}")

            except:
                st.write("Calculation Error")

        # COLUMN 4
        with c4:
            st.markdown("### 🚨 Due")
            st.write("Auto based on remaining")

    # ==============================
    # 📥 DOWNLOAD
    # ==============================
    st.download_button("📥 Download Report", df.to_csv(index=False), "report.csv")
