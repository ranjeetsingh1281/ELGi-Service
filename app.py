import streamlit as st
import pandas as pd
import os

# ==============================
# 🔐 LOGIN
# ==============================
USER_CREDENTIALS = {"admin": "1234"}

def login():
    st.title("🔐 ELGi Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USER_CREDENTIALS and USER_CREDENTIALS[u] == p:
            st.session_state["login"] = True
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
# 🧠 HELPERS
# ==============================
def fmt(dt):
    try:
        return pd.to_datetime(dt).strftime('%d-%b-%y')
    except:
        return "N/A"

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
# 🚀 DASHBOARD FUNCTION
# ==============================
def dashboard(df, title, industrial=False):

    st.title(f"🛠️ {title}")

    # ==============================
    # COLUMN DETECTION
    # ==============================
    cust_col = next((c for c in df.columns if "customer" in c.lower()), None)
    fab_col = next((c for c in df.columns if "fabrication" in c.lower()), None)
    status_col = next((c for c in df.columns if "unit status" in c.lower()), None)
    cat_col = next((c for c in df.columns if "category" in c.lower()), None)

    # ==============================
    # 📊 METRICS
    # ==============================
    if status_col:
        total = len(df)
        active = len(df[df[status_col].astype(str).str.contains("Active", case=False, na=False)])
        shifted = len(df[df[status_col].astype(str).str.contains("Shifted", case=False, na=False)])
        sold = len(df[df[status_col].astype(str).str.contains("Sold", case=False, na=False)])

        st.markdown(f"""
        | Total | Active | Shifted | Sold |
        |---|---|---|---|
        | **{total}** | **{active}** | **{shifted}** | **{sold}** |
        """)

        # Sidebar
        st.sidebar.markdown("### 📊 Unit Summary")
        st.sidebar.write(f"Total: {total}")
        st.sidebar.write(f"Active: {active}")
        st.sidebar.write(f"Shifted: {shifted}")
        st.sidebar.write(f"Sold: {sold}")

    # Category Sidebar
    if cat_col:
        st.sidebar.markdown("### 📦 Category Count")
        for k, v in df[cat_col].value_counts().items():
            st.sidebar.write(f"{k}: {v}")

    # ==============================
    # TABS
    # ==============================
    tab1, tab2, tab3 = st.tabs(["Machine Tracker", "FOC List", "Service Pending"])

    with tab1:

        if not cust_col or not fab_col:
            st.error("Required columns missing")
            return

        col1, col2 = st.columns(2)

        customers = ["All"] + sorted(df[cust_col].astype(str).unique())
        sel_c = col1.selectbox("Customer", customers)

        df_f = df if sel_c == "All" else df[df[cust_col] == sel_c]

        fabs = ["Select"] + sorted(df_f[fab_col].astype(str).unique())
        sel_f = col2.selectbox("Fabrication No", fabs)

        if sel_f != "Select":

            row = df_f[df_f[fab_col].astype(str) == sel_f].iloc[0]

            c1, c2, c3, c4 = st.columns(4)

            # ==============================
            # COLUMN 1
            # ==============================
            with c1:
                st.markdown("### **Customer Info**")
                st.write(f"**Customer:** {row.get(cust_col)}")
                st.write(f"**Model:** {row.get(next((c for c in df.columns if 'model' in c.lower()), None))}")
                st.write(f"**Location:** {row.get(next((c for c in df.columns if 'location' in c.lower()), None))}")
                st.write(f"**Running Hrs:** {row.get(next((c for c in df.columns if 'hmr' in c.lower()), None))}")

            # ==============================
            # COLUMN 2 (FIXED)
            # ==============================
            with c2:
                st.markdown("### **Replacement Dates**")

                if not industrial:
                    rep_map = {
                        "Oil": ["Oil R-Date","Oil Replacement Date"],
                        "AFC": ["AFC R-Date","Air filter Compressor Replaced Date"],
                        "AFE": ["AFE R-Date","Air filter Engine Replaced Date"],
                        "MOF": ["MOF R-Date","Main Oil filter Replaced Date"],
                        "ROF": ["ROF R-Date","Return Oil filter Replaced Date"],
                        "AOS": ["AOS R-Date","AOS Replaced Date"],
                        "RGT": ["Greasing R-Date","Greasing Done Date"],
                        "1500K": ["1500 Kit R-Date","1500 Valve kit Replaced Date"],
                        "3000K": ["3000 Kit R-Date","3000 Valve kit Replaced Date"]
                    }
                else:
                    rep_map = {
                        "Oil": ["MDA Oil R Date"],
                        "AF": ["MDA AF R Date"],
                        "OF": ["MDA OF R Date"],
                        "AOS": ["MDA AOS R Date"],
                        "RGT": ["MDA RGT R Date"],
                        "VK": ["MDA Valvekit R Date"],
                        "PF": ["MDA PF R DATE"],
                        "FF": ["MDA FF R DATE"],
                        "CF": ["MDA CF R DATE"]
                    }

                for k, options in rep_map.items():
                    col = next((c for c in df.columns if c in options), None)
                    st.write(f"**{k}:** {fmt(row.get(col)) if col else 'N/A'}")

            # ==============================
            # COLUMN 3
            # ==============================
            with c3:
                st.markdown("### **Remaining Hours**")
                st.write("**Remaining logic applied from sheet**")

            # ==============================
            # COLUMN 4 (FIXED)
            # ==============================
            with c4:
                st.markdown("### **Due Dates**")

                if not industrial:
                    due_map = {
                        "OIL":"OIL DUE DATE","AFC":"AFC DUE DATE","AFE":"AFE DUE DATE",
                        "MOF":"MOF DUE DATE","ROF":"ROF DUE DATE","AOS":"AOS DUE DATE",
                        "RGT":"RGT DUE DATE","1500K":"1500 KIT DUE DATE","3000K":"3000 KIT DUE DATE"
                    }
                else:
                    due_map = {
                        "AF":"AF DUE DATE","OF":"OF DUE DATE","OIL":"OIL DUE DATE",
                        "AOS":"AOS DUE DATE","VK":"VALVEKIT DUE DATE","RGT":"RGT DUE DATE",
                        "PF":"PF DUE DATE","FF":"FF DUE DATE","CF":"CF DUE DATE"
                    }

                for k,v in due_map.items():
                    col = next((c for c in df.columns if v in c), None)
                    st.write(f"**{k}:** {fmt(row.get(col)) if col else 'N/A'}")

            # ==============================
            # FOC
            # ==============================
            st.subheader("🎁 FOC Details")
            foc_col = next((c for c in foc_df.columns if "fabrication" in c.lower()), None)
            if foc_col:
                st.dataframe(foc_df[foc_df[foc_col].astype(str) == sel_f])

            # ==============================
            # SERVICE
            # ==============================
            st.subheader("🕒 Service History")
            serv_col = next((c for c in service_df.columns if "fabrication" in c.lower()), None)
            if serv_col:
                st.dataframe(service_df[service_df[serv_col].astype(str) == sel_f])

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
