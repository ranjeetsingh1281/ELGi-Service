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

# CLEAN
df.columns = df.columns.str.strip()

# FORCE STRING (SAFE)
df = df.astype(str)

# ================= COLUMN =================
def get_col(key):
    return next((c for c in df.columns if key.lower() in c.lower()), None)

cust_col = get_col("customer")
fab_col = get_col("fabrication")
priority_col = get_col("priority")
visit_col = get_col("visit")

# ================= FILTER =================
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

        data_list = []

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

            data_list.append({
                "Fabrication": row.get(fab_col, ""),
                "Customer": row.get(cust_col, ""),
                "Visit Date": row.get(visit_col, ""),
                "Priority": row.get(priority_col, ""),
                "Score": score
            })

        safe_df = pd.DataFrame(data_list)

        st.dataframe(safe_df, use_container_width=True)

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
