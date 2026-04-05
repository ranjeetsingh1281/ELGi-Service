import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

st.set_page_config(layout="wide")

# ================= LOGIN =================
USER_DB = {
    "admin": "admin123",
    "viewer": "demo"
}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("🔐 Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USER_DB and USER_DB[u] == p:
            st.session_state.login = True
            st.session_state.user = u
            st.rerun()
        else:
            st.error("Invalid login")

    st.stop()

st.sidebar.title(f"👋 {st.session_state.user}")

# ================= LOAD =================
df = pd.read_excel("Master_OD_Data.xlsx").fillna("")
foc = pd.read_excel("Active_FOC.xlsx").fillna("")
service = pd.read_excel("Service_Details.xlsx").fillna("")

df.columns = df.columns.str.strip()

# ================= COLUMN FIND =================
def get_col(keyword