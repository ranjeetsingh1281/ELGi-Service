import streamlit as st
import pandas as pd
import urllib.parse
from supabase import create_client, Client
from io import BytesIO


# ==============================
# 🔐 LOGIN SYSTEM
# ==============================
USER_DB = {"admin": "admin123", "user1": "dpsac123", "user2": "ind123"}

def login():
    st.title("🔐 ELGi Global - Cloud Edition")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if u in USER_DB and USER_DB[u] == p:
            st.session_state["login"], st.session_state["user"] = True, u
            st.rerun()
        else: st.error("Invalid Credentials")

if "login" not in st.session_state or not st.session_state["login"]:
    login(); st.stop()

# ==============================
# ⚙️ HELPERS
# ==============================
st.set_page_config(page_title="ELGi Global Cloud Tracker", layout="wide")

def fmt(dt):
    if not dt or dt == "N/A": return "N/A"
    return pd.to_datetime(dt).strftime('%d-%b-%y')

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# ==============================
# 📂 DATA LOADING FROM DB
# ==============================
@st.cache_data(ttl=600) # Refresh every 10 mins
def fetch_data(tracker_type):
    res = supabase.table("machines").select("*").eq("tracker_type", tracker_type).execute()
    return pd.DataFrame(res.data)

# ==============================
# 💎 TRACKER ENGINE
# ==============================
def run_tracker(df, name):
    st.title(f"🛠️ {name} Cloud Tracker")
    
    t1, t2 = st.tabs(["Machine Tracker", "⏳ Service Pending"])
    
    with t1:
        colA, colB = st.columns(2)
        sel_c = colA.selectbox(f"Customer", ["All"] + sorted(df["customer_name"].unique()))
        df_f = df if sel_c == "All" else df[df["customer_name"] == sel_c]
        sel_f = colB.selectbox(f"Fabrication Number", ["Select"] + sorted(df_f["fabrication_id"].unique()))

        if sel_f != "Select":
            row = df_f[df_f["fabrication_id"] == sel_f].iloc[0]
            m1, m2 = st.columns(2)
            with m1:
                st.info("📋 Machine Info")
                st.write(f"**Cust:** {row['customer_name']}")
                st.write(f"**Current Hours:** `{row['current_hmr']}` 📟")
                st.write(f"**Total Hours (DN):** `{row['total_hours_dn']}` 📊")
                st.write(f"**Last Service:** {fmt(row['last_service_date'])} 📅")
                
                # --- UPDATE HMR OPTION (The Power of DB) ---
                new_hmr = st.number_input("Update Live HMR:", value=float(row['current_hmr']))
                if st.button("💾 Save to Cloud"):
                    supabase.table("machines").update({"current_hmr": new_hmr}).eq("fabrication_id", sel_f).execute()
                    st.success("Cloud Updated! Refreshing...")
                    st.cache_data.clear()
                    st.rerun()

    with t2:
        st.subheader("⏳ Overdue Machines")
        # SQL logic can be added here to filter overdue
        st.dataframe(df, use_container_width=True)

# --- NAVIGATION ---
nav = st.sidebar.radio("Go to:", ["DPSAC Tracker", "INDUSTRIAL Tracker", "📢 Automation Center"])
if nav == "DPSAC Tracker": run_tracker(fetch_data("DPSAC"), "DPSAC")
elif nav == "INDUSTRIAL Tracker": run_tracker(fetch_data("INDUSTRIAL"), "INDUSTRIAL")
elif nav == "📢 Automation Center":
    st.title("📢 Broadcast Alerts")
    if st.button("📱 WhatsApp All Overdue"):
        st.info("WhatsApp API integration required.")
