import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(layout="wide")

# ================= LOGIN =================
USER_DB = {"admin": "admin123"}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if USER_DB.get(u) == p:
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Invalid Login")
    st.stop()

# ================= LOAD =================
df = pd.read_excel("Master_OD_Data.xlsx")

# CLEAN COLUMN
df.columns = df.columns.str.strip()

# ================= SAFE COLUMN FIND =================
def find_col(possible_names):
    for name in possible_names:
        for col in df.columns:
            if name.lower() in col.lower():
                return col
    return None

cust_col = find_col(["customer", "party"])
fab_col = find_col(["fabrication"])
priority_col = find_col(["priority"])
visit_col = find_col(["visit"])

# ================= SAFETY CHECK =================
if cust_col is None or fab_col is None:
    st.error("❌ Customer or Fabrication column not found in Excel")
    st.write("Available columns:", list(df.columns))
    st.stop()

# ================= FILTER =================
df = df.fillna("").astype(str)

customers = ["All"] + sorted(df[cust_col].unique())

sel = st.sidebar.selectbox("Customer", customers)

df_f = df if sel == "All" else df[df[cust_col] == sel]

# ================= DASHBOARD =================
st.title("🏭 Industrial Dashboard")
st.metric("Total Units", len(df_f))

# ================= PRIORITY =================
st.subheader("🚨 Priority Visit Dashboard")

if priority_col:

    p_df = df_f[df_f[priority_col] != ""]

    if len(p_df) > 0:

        st.success(f"{len(p_df)} Priority Visits Found")

        safe_data = []

        for _, row in p_df.iterrows():

            try:
                last = pd.to_datetime(row.get(visit_col), errors='coerce')

                if pd.isna(last):
                    score = "Unknown"
                else:
                    days = (datetime.today() - last).days

                    if days > 60:
                        score = "🔴 High"
                    elif days > 30:
                        score = "🟡 Medium"
                    else:
                        score = "🟢 Normal"

            except:
                score = "Unknown"

            safe_data.append({
                "Fabrication": row.get(fab_col, ""),
                "Customer": row.get(cust_col, ""),
                "Visit Date": row.get(visit_col, ""),
                "Priority": row.get(priority_col, ""),
                "Score": score
            })

        safe_df = pd.DataFrame(safe_data)

        st.dataframe(safe_df)

        # EXPORT
        buf = BytesIO()
        safe_df.to_excel(buf, index=False)

        st.download_button("📥 Download Priority", buf.getvalue())

    else:
        st.warning("No Priority Data")

# ================= MACHINE =================
st.subheader("🔍 Machine Tracker")

machines = ["Select"] + list(df_f[fab_col].unique())

sel_f = st.selectbox("Machine", machines)

if sel_f != "Select":

    row_df = df_f[df_f[fab_col] == sel_f]

    if len(row_df) > 0:
        row = row_df.iloc[0]

        st.json(dict(row))