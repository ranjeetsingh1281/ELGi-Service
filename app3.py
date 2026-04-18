import streamlit as st
import pandas as pd
from datetime import datetime
import urllib.parse
from io import BytesIO

# ==============================
# 🔐 LOGIN
# ==============================
USER_DB = {
    "admin": "admin123",
    "user": "123"
}

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
# CONFIG
# ==============================
st.set_page_config(layout="wide")

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
        if val < 0: return f"🔴 {val}"
        elif val <= 200: return f"🟡 {val}"
        else: return f"🟢 {val}"
    except:
        return "N/A"

def smart_get(row, keys):
    for col in row.index:
        c = str(col).lower().replace(" ","").replace("-","")
        if all(k in c for k in keys):
            return row[col]
    return "N/A"

def predict(row):
    try:
        hmr = smart_get(row, ["hmr"])
        avg = smart_get(row, ["avg"])

        if hmr == "N/A" or avg == "N/A":
            return "N/A"

        remaining = 2000 - float(hmr)
        days = remaining / float(avg)

        return (datetime.today() + pd.Timedelta(days=days)).strftime("%d-%b-%Y")
    except:
        return "N/A"

def to_excel(df):
    buf = BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

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
# SIDEBAR
# ==============================
st.sidebar.title(f"👋 {st.session_state['user']}")

menu = st.sidebar.radio("Menu", [
    "Dashboard",
    "Machine Tracker",
    "FOC List",
    "Overdue",
    "📢 Alerts"
])

if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# ==============================
# DASHBOARD
# ==============================
if menu == "Dashboard":

    st.title("📊 ELGi Premium Dashboard")

    status_col = next((c for c in master.columns if "status" in c.lower()), None)

    total = len(master)
    active = len(master[master[status_col].str.contains("active", case=False, na=False)])
    shifted = len(master[master[status_col].str.contains("shifted", case=False, na=False)])
    sold = len(master[master[status_col].str.contains("sold", case=False, na=False)])

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total", total)
    c2.metric("Active", active)
    c3.metric("Shifted", shifted)
    c4.metric("Sold", sold)

    st.subheader("📊 Status Chart")
    st.bar_chart(master[status_col].value_counts())

    st.subheader("📈 HMR Trend")
    hmr_col = next((c for c in master.columns if "hmr" in c.lower()), None)
    if hmr_col:
        st.line_chart(master[hmr_col])

# ==============================
# MACHINE TRACKER
# ==============================
elif menu == "Machine Tracker":

    cust_col = next((c for c in master.columns if "customer" in c.lower()), master.columns[0])
    fab_col = next((c for c in master.columns if "fabrication" in c.lower()), master.columns[1])

    c1,c2 = st.columns(2)

    sel_c = c1.selectbox("Customer", ["All"] + sorted(master[cust_col].astype(str).unique()))
    df_f = master if sel_c=="All" else master[master[cust_col]==sel_c]

    sel_f = c2.selectbox("Fabrication", ["Select"] + sorted(df_f[fab_col].astype(str).unique()))

    if sel_f != "Select":

        row = df_f[df_f[fab_col]==sel_f].iloc[0]

        col1,col2,col3,col4 = st.columns(4)

        parts = ["oil","afc","afe","mof","rof","aos","rgt","1500","3000"]

        with col1:
            st.markdown("### 📋 Info")
            st.write(row[cust_col])
            st.write("🔮 Next Failure:", predict(row))

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

        # FOC
        st.subheader("🎁 FOC")
        foc_cols = [c for c in foc.columns if any(k in c.lower() for k in ["fabrication","part","qty","date"])]
        f_fab = next((c for c in foc.columns if "fabrication" in c.lower()), foc.columns[0])
        st.dataframe(foc[foc[f_fab]==sel_f][foc_cols])

        # Service
        st.subheader("🕒 Service")
        s_fab = next((c for c in service.columns if "fabrication" in c.lower()), service.columns[0])
        st.dataframe(service[service[s_fab]==sel_f])

# ==============================
# FOC LIST
# ==============================
elif menu == "FOC List":
    st.dataframe(foc)

# ==============================
# OVERDUE
# ==============================
elif menu == "Overdue":

    over_col = next((c for c in master.columns if "over" in c.lower()), None)

    if over_col:
        master[over_col] = pd.to_numeric(master[over_col], errors='coerce').fillna(0)
        df_o = master[master[over_col] > 0]

        st.warning(f"{len(df_o)} Machines Overdue")
        st.dataframe(df_o)

        st.download_button("Download", to_excel(df_o), "Overdue.xlsx")

# ==============================
# ALERT
# ==============================
elif menu == "📢 Alerts":

    msg = st.text_area("Message", "Service Due Alert")

    wa_link = f"https://wa.me/91XXXXXXXXXX?text={urllib.parse.quote(msg)}"

    st.markdown(f"[📱 Send WhatsApp]({wa_link})")
