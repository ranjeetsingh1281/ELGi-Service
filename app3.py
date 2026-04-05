import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table

st.set_page_config(layout="wide")

# ================= LOAD =================
df = pd.read_excel("Master_OD_Data.xlsx").fillna("")
foc = pd.read_excel("Active_FOC.xlsx").fillna("")
service = pd.read_excel("Service_Details.xlsx").fillna("")

df.columns = df.columns.str.strip()

# ================= COLUMN FIND =================
def get_col(keyword):
    return next((c for c in df.columns if keyword.lower() in c.lower()), None)

cust_col = get_col("customer")
fab_col = get_col("fabrication")
status_col = get_col("status")
cat_col = get_col("category")
w_col = get_col("warranty")
amc_col = get_col("amc")

# ================= FILTER =================
df[cust_col] = df[cust_col].astype(str)
df[fab_col] = df[fab_col].astype(str)

customers = ["All"] + sorted(df[cust_col].unique())
sel = st.sidebar.selectbox("Customer", customers)

df_f = df if sel == "All" else df[df[cust_col] == sel]

# ================= EXPORT =================
def to_excel(df):
    buf = BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

def to_pdf(df):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf)
    data = [df.columns.tolist()] + df.astype(str).values.tolist()
    table = Table(data)
    doc.build([table])
    return buf.getvalue()

# ================= DASHBOARD =================
st.title("🏭 Industrial Dashboard")

st.metric("Total Units", len(df_f))

if status_col:
    st.sidebar.write(df_f[status_col].value_counts())

if cat_col:
    st.sidebar.write(df_f[cat_col].value_counts())

# ================= WARRANTY =================
st.sidebar.subheader("📅 Warranty Expiry")

if w_col:
    df_f[w_col] = pd.to_datetime(df_f[w_col], errors='coerce')
    df_f["Warranty End"] = df_f[w_col] + pd.DateOffset(years=1)

    df_valid = df_f.dropna(subset=["Warranty End"])

    if not df_valid.empty:
        year = st.sidebar.selectbox("Year", sorted(df_valid["Warranty End"].dt.year.unique()))
        df_year = df_valid[df_valid["Warranty End"].dt.year == year]

        monthly = df_year["Warranty End"].dt.month.value_counts().sort_index()
        st.sidebar.write(monthly)

        st.sidebar.download_button("Warranty Excel", to_excel(df_year))
        st.sidebar.download_button("Warranty PDF", to_pdf(df_year))

# ================= AMC =================
st.sidebar.subheader("📆 AMC Expired")

if amc_col:
    df_f[amc_col] = pd.to_datetime(df_f[amc_col], errors='coerce')
    df_amc = df_f[df_f[amc_col] < datetime.today()]

    st.sidebar.write(df_amc[amc_col].dt.month.value_counts().sort_index())

    st.sidebar.download_button("AMC Excel", to_excel(df_amc))
    st.sidebar.download_button("AMC PDF", to_pdf(df_amc))

# ================= MACHINE =================
st.subheader("🔍 Machine Tracker")

machines = ["Select"] + list(df_f[fab_col].unique())
sel_f = st.selectbox("Machine", machines)

if sel_f != "Select":

    row = df_f[df_f[fab_col] == sel_f].iloc[0]
    st.dataframe(pd.DataFrame([row]))

    # ================= PARTS =================
    st.subheader("🔧 Parts")

    parts = ["AF","OF","OIL","AOS","RGT","VK","PF","FF","CF"]

    for part in parts:

        rem_col = next((c for c in df.columns if part.lower() in c.lower() and "rem" in c.lower()), None)
        due_col = next((c for c in df.columns if part.lower() in c.lower() and "due" in c.lower()), None)

        rem = row.get(rem_col, None)
        due = row.get(due_col, None)

        color = "🟢"
        try:
            if float(rem) < 200:
                color = "🔴"
            elif float(rem) < 500:
                color = "🟡"
        except:
            pass

        overdue = ""
        try:
            if pd.to_datetime(due) < pd.Timestamp.today():
                overdue = "⚠️ OVERDUE"
        except:
            pass

        st.write(f"{color} {part} → Remaining: {rem} | Due: {due} {overdue}")

    # ================= AI PREDICTION =================
    st.subheader("🤖 AI Prediction")

    try:
        hmr = float(row.get("HMR", 0))
        predicted = hmr + 500
        st.success(f"Next service expected at {int(predicted)} Hrs")
    except:
        st.info("No prediction data")

# ================= CHART =================
if status_col:
    fig = px.pie(df_f, names=status_col)
    st.plotly_chart(fig)

# ================= WHATSAPP ALERT (SIMULATION) =================
st.subheader("📲 WhatsApp Alert")

if st.button("Send Overdue Alert"):
    st.success("✅ WhatsApp Alert Sent (API Ready)")