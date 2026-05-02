import streamlit as st
import pandas as pd
from io import BytesIO

# --- 1. MODERN PAGE CONFIG ---
st.set_page_config(page_title="PRIME POWER CRM Pro", layout="wide", initial_sidebar_state="expanded")

# --- 2. GLASS UI & VISIBILITY CSS ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.95) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    /* Sidebar Text Fix */
    [data-testid="stSidebar"] label p { color: #ffffff !important; font-weight: 700 !important; }
    [data-testid="stSidebar"] div[data-baseweb="select"] div { color: #0f172a !important; font-weight: 600 !important; }
    
    /* KPI Metric Cards */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.07) !important;
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.3s ease;
    }
    [data-testid="stMetric"]:hover { transform: translateY(-5px); }
    div[data-testid="stMetricValue"] > div { color: #38bdf8 !important; font-weight: 800; }
    
    h1, h2, h3, h4, p, span { color: #f8fafc !important; }
    .stTable { background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        master = pd.read_excel("Master_Data.xlsx")
        service = pd.read_excel("Service_Details.xlsx")
        foc = pd.read_excel("Active_FOC.xlsx")
        return master, service, foc
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

master, service, foc = load_data()

# --- HELPERS ---
def format_date(val):
    if pd.isna(val) or str(val).strip() == "" or val == "N/A": return "N/A"
    try: return pd.to_datetime(val).strftime('%d-%b-%y')
    except: return str(val)

def find_col(df, kws):
    for c in df.columns:
        if any(k.lower() in str(c).lower() for k in kws): return c
    return None

# Clean Columns
for df in [master, service, foc]:
    if not df.empty: df.columns = df.columns.str.strip()

# Detect Critical Columns
cust_col = find_col(master, ["customer name", "customer"]) or "CUSTOMER NAME"
mach_col = find_col(master, ["fabrication", "fab no"]) or "FABRICATION NO."
warr_type_col = find_col(master, ["warranty type", "warranty pd"]) or "Warranty Type"
warr_exp_col = find_col(master, ["warranty expires", "warranty exp"]) or "Warranty Expires on"

# --- SIDEBAR REDESIGN ---
with st.sidebar:
    st.markdown("### 🛠️ Control Panel")
    
    # Category Filter
    if "Category" in master.columns:
        cat_list = ["All"] + sorted(master["Category"].dropna().unique().tolist())
        sel_cat = st.selectbox("📁 Category", cat_list)
        if sel_cat != "All": master = master[master["Category"] == sel_cat]

    # Customer & Machine Logic
    sel_cust = st.selectbox("👤 Customer", ["All"] + sorted(master[cust_col].dropna().unique().tolist()))
    f_master = master.copy()
    if sel_cust != "All": f_master = master[master[cust_col] == sel_cust]
    
    sel_mach = st.selectbox("⚙️ Track Fabrication No.", ["All"] + sorted(f_master[mach_col].dropna().astype(str).unique().tolist()))

    st.markdown("---")
    # Warranty Expiry Sidebar Table
    st.markdown("### 📅 Warranty Expiry Tracker")
    if warr_exp_col in master.columns:
        master[warr_exp_col] = pd.to_datetime(master[warr_exp_col], errors='coerce')
        valid_dates = master[master[warr_exp_col].notna()]
        if not valid_dates.empty:
            years = sorted(valid_dates[warr_exp_col].dt.year.unique().tolist(), reverse=True)
            sel_year = st.selectbox("Filter Expiry Year", years)
            
            # Month-wise count
            year_data = valid_dates[valid_dates[warr_exp_col].dt.year == sel_year]
            monthly = year_data[warr_exp_col].dt.strftime('%B').value_counts().reindex([
                "January", "February", "March", "April", "May", "June", 
                "July", "August", "September", "October", "November", "December"
            ]).fillna(0).astype(int)
            st.table(monthly.rename("Units"))
        else: st.info("No expiry dates found.")

# --- MAIN DASHBOARD ---
st.markdown('<h1 style="color:#38bdf8; font-size:3rem; font-weight:800; margin-bottom:0;">PRIME POWER CRM PRO</h1>', unsafe_allow_html=True)
st.markdown("---")

# 1) Animated KPI Cards
col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("👥 Total Customers", filtered_master[customer_col].nunique())
col2.metric("🏗️ Total Machines", filtered_master[machine_col].nunique())

if "Unit Status" in f_master.columns:
    status = f_master["Unit Status"].value_counts()
    col3.metric("🚚 Active", status_counts.get("Active", 0))
    col4.metric("🗑️ Scraped", status_counts.get("Scraped", 0))
    col5.metric("🚔 Shifted", status_counts.get("Shifted", 0))
    col6.metric("❌ Sold", status_counts.get("Sold", 0))

# 2) Warranty Type Count
st.markdown("#### 🛡️ Warranty Breakdown")
if warr_type_col in f_master.columns:
    w_counts = f_master[warr_type_col].value_counts()
    w_cols = st.columns(len(w_counts) if not w_counts.empty else 1)
    for i, (name, count) in enumerate(w_counts.items()):
        w_cols[i % len(w_cols)].markdown(f"**{name}:** `{count}`")
st.markdown("---")

# 3) 4-Column Tracker (When Machine Selected)
if sel_mach != "All":
    m_data = master[master[mach_col].astype(str) == str(sel_mach)].iloc[0]
    st.subheader(f"💎 Live Tracking: {sel_mach}")
    
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.markdown('<div style="background:rgba(56,189,248,0.1); padding:10px; border-left:5px solid #38bdf8; border-radius:5px;"><b>👤 Customer Info</b></div>', unsafe_allow_html=True)
        st.write(f"**Name:** {m_data.get('CUSTOMER NAME','N/A')}")
        st.write(f"**Address:** {m_data.get('Address','N/A')}")
        st.write(f"**Contact:** {m_data.get('Contact No. 1','N/A')}")
        st.write(f"**Last Service:** {format_date(m_data.get('Last Service Date'))}")
    
    with t2:
        st.markdown('<div style="background:rgba(251,191,36,0.1); padding:10px; border-left:5px solid #fbbf24; border-radius:5px;"><b>📅 Last Replacement</b></div>', unsafe_allow_html=True)
        for r_col in ["Oil R Date", "AFC R Date", "AFE R Date", "MOF R Date"]:
            st.write(f"**{r_col}:** {format_date(m_data.get(r_col))}")
            
    with t3:
        st.markdown('<div style="background:rgba(52,211,153,0.1); padding:10px; border-left:5px solid #34d399; border-radius:5px;"><b>⏳ LIVE Remaining</b></div>', unsafe_allow_html=True)
        for l_col in ["LIVE - Oil remaining", "LIVE - Separator remaining"]:
            st.write(f"**{l_col}:** {m_data.get(l_col, '0')}")
            
    with t4:
        st.markdown('<div style="background:rgba(248,113,113,0.1); padding:10px; border-left:5px solid #f87171; border-radius:5px;"><b>🚨 Next Due Dates</b></div>', unsafe_allow_html=True)
        for d_col in ["OIL DUE DATE", "AOS DUE DATE"]:
            st.write(f"**{d_col}:** {format_date(m_data.get(d_col))}")

    st.markdown("---")

    # 4) Recent Service Requests (Expander Logic)
    st.subheader("🛠️ Recent Service Requests")
    svc_fab = find_col(service, ["fabrication"])
    if svc_fab:
        s_display = service[service[svc_fab].astype(str) == str(sel_mach)].copy()
        if not s_display.empty:
            if "Call Logged Date" in s_display.columns: s_display = s_display.sort_values("Call Logged Date", ascending=False)
            for _, row in s_display.head(5).iterrows():
                with st.expander(f"📅 {format_date(row.get('Call Logged Date'))} | {row.get('Call Type','N/A')}"):
                    st.info(row.get("Service Engineer Comments", "No comments available."))
        else: st.info("No service history.")

    # 5) FOC Details
    st.subheader("📦 FOC Details")
    foc_fab = find_col(foc, ["fabrication"])
    if foc_fab:
        f_display = foc[foc[foc_fab].astype(str) == str(sel_mach)]
        if not f_display.empty:
            f_cols = ["Created On", "FOC Number", "Customer Name", "MODEL", "FABRICATION NO.", "Part Code"]
            st.dataframe(f_display[[c for c in f_cols if c in f_display.columns]], use_container_width=True)
else:
    st.info("👋 Welcome! Please select a machine from the sidebar to view full intelligence.")
