import streamlit as st
import pandas as pd
from io import BytesIO
import urllib.parse
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib import colors

# ==============================
# CONFIG
# ==============================
st.set_page_config(layout="wide")

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
# EXPORT FUNCTIONS
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
# LOAD DATA
# ==============================
master = pd.read_excel("Master_Data.xlsx")
od = pd.read_excel("Master_OD_Data.xlsx")
foc = pd.read_excel("Active_FOC.xlsx")

master.columns = master.columns.str.strip()
od.columns = od.columns.str.strip()
foc.columns = foc.columns.str.strip()

# ==============================
# COLUMN DETECT
# ==============================
cust_col = next((c for c in master.columns if "customer" in c.lower()), master.columns[0])
status_col = next((c for c in master.columns if "status" in c.lower()), None)
cat_col = next((c for c in master.columns if "category" in c.lower()), None)
fab_col = next((c for c in master.columns if "fabrication" in c.lower()), master.columns[1])
over_col = next((c for c in master.columns if "over" in c.lower()), None)

cust_col_od = next((c for c in od.columns if "customer" in c.lower()), od.columns[0])
fab_col_od = next((c for c in od.columns if "fabrication" in c.lower()), od.columns[1])
over_col_od = next((c for c in od.columns if "over" in c.lower()), None)

# ==============================
# SIDEBAR
# ==============================
st.sidebar.title(f"👋 {st.session_state['user']} ({role})")

menu = st.sidebar.radio("Select Tracker", ["DPSAC Tracker", "Industrial Tracker"])

# ==============================
# DPSAC TRACKER
# ==============================
if menu == "DPSAC Tracker":

    st.title("📊 DPSAC Dashboard")

    customers = ["All"] + sorted(master[cust_col].astype(str).unique())
    sel = st.selectbox("Customer", customers)

    df = master if sel == "All" else master[master[cust_col] == sel]

    # KPI
    total = len(df)
    active = len(df[df[status_col].str.contains("active", case=False, na=False)])
    shifted = len(df[df[status_col].str.contains("shifted", case=False, na=False)])
    sold = len(df[df[status_col].str.contains("sold", case=False, na=False)])

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total", total)
    c2.metric("Active", active)
    c3.metric("Shifted", shifted)
    c4.metric("Sold", sold)

    # Category
    if cat_col:
        st.subheader("Category Count")
        st.dataframe(df[cat_col].value_counts())

    # Machine Tracker
    st.subheader("Machine Tracker")
    sel_f = st.selectbox("Fabrication", ["Select"] + list(df[fab_col].astype(str).unique()))

    if sel_f != "Select":
        st.dataframe(df[df[fab_col] == sel_f])

    # FOC
    st.subheader("FOC List")
    st.dataframe(foc)

    # Overdue
    if over_col:
        master[over_col] = pd.to_numeric(master[over_col], errors='coerce').fillna(0)
        overdue = master[master[over_col] > 0]

        st.subheader("Overdue Service")
        st.dataframe(overdue)

    # Export
    if role != "viewer":
        st.download_button("Excel", to_excel(df), "dpsac.xlsx")
        st.download_button("PDF", to_pdf(df), "dpsac.pdf")

# ==============================
# INDUSTRIAL TRACKER
# ==============================
else:

    st.title("🏭 Industrial Tracker")

    customers = ["All"] + sorted(od[cust_col_od].astype(str).unique())
    sel = st.selectbox("Customer", customers)

    df = od if sel == "All" else od[od[cust_col_od] == sel]

    # Tracker
    sel_f = st.selectbox("Fabrication", ["Select"] + list(df[fab_col_od].astype(str).unique()))

    if sel_f != "Select":
        st.dataframe(df[df[fab_col_od] == sel_f])

    # FOC
    st.subheader("Industrial FOC List")
    st.dataframe(foc)

    # Overdue
    if over_col_od:
        od[over_col_od] = pd.to_numeric(od[over_col_od], errors='coerce').fillna(0)
        overdue = od[od[over_col_od] > 0]

        st.subheader("Industrial Overdue")
        st.dataframe(overdue)

    # Export
    if role != "viewer":
        st.download_button("Excel", to_excel(df), "industrial.xlsx")
        st.download_button("PDF", to_pdf(df), "industrial.pdf")

# ==============================
# ALERT
# ==============================
st.subheader("📢 WhatsApp Alert")

msg = st.text_area("Message", "Service Due Alert")

if role != "viewer":
    wa = f"https://wa.me/917061158953?text={urllib.parse.quote(msg)}"
    st.markdown(f"[Send WhatsApp]({wa})")
else:
    st.info("Viewer Mode: Alert disabled")