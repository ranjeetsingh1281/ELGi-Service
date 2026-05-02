import streamlit as st
import pandas as pd
from io import BytesIO

# --- MODERN PAGE CONFIG ---
st.set_page_config(page_title="PRIME POWER CRM Pro", layout="wide", initial_sidebar_state="expanded")

# --- SIDEBAR FONT VISIBILITY FIX ---
st.markdown("""
    <style>
    /* Global Background & Dark Mode feel */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc !important;
    }
    
    /* Sidebar Background (Glassmorphism) */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.95) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Sidebar Labels (Category, Customer, Fabrication No.) */
    /* Ise white rakhenge kyunki sidebar background dark hai */
    [data-testid="stSidebar"] label p {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }

    /* Sidebar Dropdown Input Text (Inside white boxes) */
    /* Yeh important hai: Box white hai toh text black hona chahiye */
    [data-testid="stSidebar"] div[data-baseweb="select"] div {
        color: #0f172a !important; /* Deep Dark Blue/Black */
        font-weight: 600 !important;
    }

    /* Sidebar Icons & Titles */
    [data-testid="stSidebar"] h3 {
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }

    /* Global Text Fix for main dashboard */
    h1, h2, h4, h5, p, span {
        color: #f8fafc !important;
    }

    /* Metric Cards Styling */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.07) !important;
        backdrop-filter: blur(10px);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    div[data-testid="stMetricValue"] > div {
        color: #38bdf8 !important;
        font-weight: 800;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        master = pd.read_excel("Master_Data.xlsx")
        service = pd.read_excel("Service_Details.xlsx")
        foc = pd.read_excel("Active_FOC.xlsx")
        return master, service, foc
    except Exception as e:
        st.error(f"Error loading Excel files: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

master, service, foc = load_data()

# Clean columns
for df in [master, service, foc]:
    if not df.empty: df.columns = df.columns.str.strip()

# Helpers
def format_date(val):
    if pd.isna(val) or val == "N/A" or str(val).strip() == "": return "N/A"
    try: return pd.to_datetime(val).strftime('%d-%b-%y')
    except: return str(val)

def find_column(df, keywords):
    for col in df.columns:
        if any(kw.lower() in str(col).lower() for kw in keywords): return col
    return None

# --- SIDEBAR REDESIGN ---
with st.sidebar:
    st.image("https://www.elgi.com/wp-content/themes/elgi/assets/images/elgi-logo.png", width=150)
    st.markdown("### 🛠️ Control Panel")
    
    customer_col = find_column(master, ["customer name", "customer"]) or "CUSTOMER NAME"
    machine_col = find_column(master, ["fabrication", "fab no"]) or "FABRICATION NO."
    category_col = find_column(master, ["category", "model group"]) or "Category"

    # Category Filter
    cat_list = ["All"] + sorted(master[category_col].dropna().unique().tolist()) if category_col in master.columns else ["All"]
    selected_category = st.selectbox("📁 Category", cat_list)
    if selected_category != "All":
        master = master[master[category_col] == selected_category]

    # Customer Filter
    cust_list = ["All"] + sorted(master[customer_col].dropna().unique().tolist())
    selected_customer = st.selectbox("👤 Customer", cust_list)

    # Machine Filter
    filtered_master = master.copy()
    if selected_customer != "All":
        filtered_master = master[master[customer_col] == selected_customer]

    machine_list = ["All"] + sorted(filtered_master[machine_col].dropna().astype(str).unique().tolist())
    selected_machine = st.selectbox("⚙️ Track Fabrication No.", machine_list)

# --- DASHBOARD LAYOUT ---
st.markdown('<h1 class="main-title">PRIME POWER CRM PRO</h1>', unsafe_allow_html=True)

# 1) Animated KPI Cards
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total Customers", filtered_master[customer_col].nunique())
col2.metric("Total Machines", filtered_master[machine_col].nunique())

if "Unit Status" in filtered_master.columns:
    status_counts = filtered_master["Unit Status"].value_counts()
    col3.metric("🚚 Active", status_counts.get("Active", 0))
    col4.metric("🗑️ Scraped", status_counts.get("Scraped", 0))
    col5.metric("🚔 Shifted", status_counts.get("Shifted", 0))
    col6.metric("❌ Sold", status_counts.get("Sold", 0))

st.markdown("---")

# 2) Glass UI 4-Column Tracker
if selected_machine != "All":
    m_data = master[master[machine_col].astype(str) == str(selected_machine)].iloc[0]
    st.subheader(f"💎 Live Tracking: {selected_machine}")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""<div style="background:rgba(56,189,248,0.1); padding:15px; border-radius:10px; border-left:5px solid #38bdf8;">
            <h4 style="margin:0;">👤 Customer Info</h4></div>""", unsafe_allow_html=True)
        st.write(f"**Customer:** {m_data.get('CUSTOMER NAME', 'N/A')}")
        st.write(f"**Address:** {m_data.get('Address', 'N/A')}")
        st.write(f"**Email:** {m_data.get('EMAIL ID', 'N/A')}")
        st.write(f"**Contact:** {m_data.get('Contact No. 1', 'N/A')}")
        st.write(f"**Last Service Date:** {format_date(m_data.get('Last Service Date'))}")
        st.write(f"**Last Service HMR:** {m_data.get('Last Service HMR', 'N/A')}")
        st.write(f"**Avg. Hrs:** {m_data.get('Avg. Hrs', '0')}")
        st.write(f"**HMR Cal.:** {m_data.get('HMR Cal.', 'N/A')}")

    with c2:
        st.markdown("""<div style="background:rgba(251,191,36,0.1); padding:15px; border-radius:10px; border-left:5px solid #fbbf24;">
            <h4 style="margin:0;">📅 Last Replacement</h4></div>""", unsafe_allow_html=True)
        for col in ["Oil R Date", "AFC R Date", "AFE R Date", "MOF R Date", "ROF R Date", "AOS R Date", "RGT R Date", "1500 kit R Date", "3000 kit R Date"]:
            st.write(f"**{col}:** {format_date(m_data.get(col))}")

    with c3:
        st.markdown("""<div style="background:rgba(52,211,153,0.1); padding:15px; border-radius:10px; border-left:5px solid #34d399;">
            <h4 style="margin:0;">⏳ LIVE Remaining</h4></div>""", unsafe_allow_html=True)
        for col in ["LIVE - Oil remaining", "LIVE - Air filter replaced - Compressor Remaining Hours", "LIVE - Air filter replaced - Engine Remaining Hours", "LIVE - Main Oil filter Remaining Hours", "LIVE - Return Oil filter Remaining Hours", "LIVE - Separator remaining", "LIVE - Motor regressed remaining", "LIVE - 1500 Valve kit Remaining Hours", "LIVE - 3000 Valve kit Remaining Hours"]:
            st.write(f"**{col}:** {m_data.get(col, '0')}")

    with c4:
        st.markdown("""<div style="background:rgba(248,113,113,0.1); padding:15px; border-radius:10px; border-left:5px solid #f87171;">
            <h4 style="margin:0;">🚨 Next Due Dates</h4></div>""", unsafe_allow_html=True)
        for col in ["OIL DUE DATE", "AFC DUE DATE", "AFE DUE DATE", "MOF DUE DATE", "ROF DUE DATE", "AOS DUE DATE", "RGT DUE DATE", "1500 KIT DUE DATE", "3000 KIT DUE DATE"]:
            st.write(f"**{col}:** {format_date(m_data.get(col))}")

    st.markdown("---")

    # 3) Recent Service Requests (Modern Expanders)
    st.subheader("🛠️ Service Intelligence")
    svc_fab_col = find_column(service, ["fabrication"])
    if svc_fab_col:
        svc_display = service[service[svc_fab_col].astype(str) == str(selected_machine)].head(5)
        for _, row in svc_display.iterrows():
            with st.expander(f"📌 {format_date(row.get('Call Logged Date'))} | {row.get('Call Type','Service')}"):
                st.write(f"**Comment:** {row.get('Service Engineer Comments', 'N/A')}")

    # 4) FOC Tracker (Glass Table)
    st.subheader("📦 FOC Status Tracker")
    foc_fab_col = find_column(foc, ["fabrication"])
    if foc_fab_col:
        foc_display = foc[foc[foc_fab_col].astype(str) == str(selected_machine)]
        st.dataframe(foc_display, use_container_width=True)
else:
    st.info("👋 Welcome BOSS! Sidebar se machine select karein tracking shuru karne ke liye.")
