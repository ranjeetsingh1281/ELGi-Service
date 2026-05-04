import streamlit as st
import pandas as pd
from io import BytesIO

# --- 1. MODERN PAGE CONFIG ---
st.set_page_config(page_title="PRIME POWER CRM Pro", layout="wide", initial_sidebar_state="expanded")

# --- 2. GLASS UI & VISIBILITY CSS ---
# --- CRIMSON UI CSS UPDATE ---
st.markdown("""
    <style>
    /* Global Background changed to Crimson Gradient */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #8b0000 0%, #dc143c 100%);
        color: #f8fafc !important;
    }
    
    /* Sidebar Background (Slightly darker Crimson) */
    [data-testid="stSidebar"] {
        background-color: rgba(60, 0, 0, 0.95) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Rest of the CSS remains same for visibility */
    [data-testid="stSidebar"] label p { color: #ffffff !important; font-weight: 700 !important; }
    [data-testid="stSidebar"] div[data-baseweb="select"] div { color: #0f172a !important; font-weight: 600 !important; }
    
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; font-weight: 800; }
    
    h1, h2, h3, h4, p, span { color: #ffffff !important; }
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

# Clean Columns
for df in [master, service, foc]:
    if not df.empty: df.columns = df.columns.str.strip()

# Helper Functions
def format_date(val):
    if pd.isna(val) or str(val).strip() == "" or val == "N/A": return "N/A"
    try: return pd.to_datetime(val).strftime('%d-%b-%y')
    except: return str(val)

def find_col(df, kws):
    for c in df.columns:
        if any(k.lower() in str(c).lower() for k in kws): return c
    return None

# Detect Columns
cust_col = find_col(master, ["customer name", "customer"]) or "CUSTOMER NAME"
mach_col = find_col(master, ["fabrication", "fab no"]) or "FABRICATION NO."
warr_type_col = find_col(master, ["warranty type", "warranty pd"]) or "Warranty Type"
warr_exp_col = find_col(master, ["warranty expires", "warranty exp"]) or "Warranty Expires on"

# --- SIDEBAR WITH LOGOS ---
with st.sidebar:
    # Dono logos ko side-by-side dikhane ke liye columns
    log_col1, log_col2 = st.columns(2)
    
    try:
        with log_col1:
            # Prime Power Logo
            st.image("input_file_0.png", use_container_width=True)
        
        with log_col2:
            # ELGi Logo
            st.image("input_file_2.png", use_container_width=True)
    except Exception as e:
        st.warning("Logo files missing! Please upload 'input_file_2.png' and 'input_file_0.png' to your folder.")
        
with st.sidebar:
    st.markdown("### 🛠️ Control Panel")
    
    # Category Filter
    if "Category" in master.columns:
        cat_list = ["All"] + sorted(master["Category"].dropna().unique().tolist())
        sel_cat = st.selectbox("📁 Category", cat_list)
        if sel_cat != "All": master = master[master["Category"] == sel_cat]

    sel_cust = st.selectbox("👤 Customer", ["All"] + sorted(master[cust_col].dropna().unique().tolist()))
    
    f_master = master.copy()
    if sel_cust != "All": f_master = master[master[cust_col] == sel_cust]
    
    sel_mach = st.selectbox("⚙️ Track Fabrication No.", ["All"] + sorted(f_master[mach_col].dropna().astype(str).unique().tolist()))

    st.markdown("---")
    # Warranty Tracker Table
    st.markdown("### 📅 Warranty Expiry Tracker")
    if warr_exp_col in master.columns:
        master[warr_exp_col] = pd.to_datetime(master[warr_exp_col], errors='coerce')
        valid_dates = master[master[warr_exp_col].notna()]
        if not valid_dates.empty:
            years = sorted(valid_dates[warr_exp_col].dt.year.unique().tolist(), reverse=True)
            sel_year = st.selectbox("Filter Expiry Year", years)
            
            year_data = valid_dates[valid_dates[warr_exp_col].dt.year == sel_year]
            monthly = year_data[warr_exp_col].dt.strftime('%B').value_counts().reindex([
                "January", "February", "March", "April", "May", "June", 
                "July", "August", "September", "October", "November", "December"
            ]).fillna(0).astype(int)
            st.table(monthly.rename("Units"))

# --- MAIN DASHBOARD ---
st.markdown('<h1 style="color:#38bdf8; font-size:3rem; font-weight:800;">PRIME POWER CRM PRO</h1>', unsafe_allow_html=True)
st.markdown("---")

# 1) Metrics Section - FIXED TYPO HERE (kpi1 instead of kpii1)
kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
kpi1.metric("👤 Total Customers", f_master[cust_col].nunique())
kpi2.metric("⚙️ Total Machines", f_master[mach_col].nunique())

if "Unit Status" in f_master.columns:
    status = f_master["Unit Status"].value_counts()
    kpi3.metric("🚚 Active", status.get("Active", 0))
    kpi4.metric("🗑️ Scraped", status.get("Scraped", 0))
    kpi5.metric("🚔 Shifted", status.get("Shifted", 0))
    kpi6.metric("❌ Sold", status.get("Sold", 0))

st.markdown("---")

# 2) 4-Column Tracker (When Machine Selected)
if sel_mach != "All":
    m_data = master[master[mach_col].astype(str) == str(sel_mach)].iloc[0]
    st.subheader(f"💎 Live Tracking: {sel_mach}")
    
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.write(f"**Customer:** {m_data.get('CUSTOMER NAME', 'N/A')}")
        st.write(f"**Address:** {m_data.get('Address', 'N/A')}")
        st.write(f"**Email:** {m_data.get('EMAIL ID', 'N/A')}")
        st.write(f"**Contact:** {m_data.get('Contact No. 1', 'N/A')}")
        st.write(f"**Last Service Date:** {format_date(m_data.get('Last Service Date'))}")
        st.write(f"**Last Service HMR:** {m_data.get('Last Service HMR', 'N/A')}")
        st.write(f"**Avg. Hrs:** {m_data.get('Avg. Hrs', '0')}")
        st.write(f"**HMR Cal.:** {m_data.get('HMR Cal.', 'N/A')}")
    
    with t2:
        st.warning("📅 Last Replacement")
        for r_col in ["Oil R Date", "AFC R Date", "AFE R Date", "MOF R Date", "ROF R Date", "AOS R Date", "RGT R Date", "1500 kit R Date", "3000 kit R Date"]:
            st.write(f"**{r_col}:** {format_date(m_data.get(r_col))}")
            
    with t3:
        st.success("⏳ LIVE Remaining")
        for l_col in ["LIVE - Oil remaining", "LIVE - Air filter replaced - Compressor Remaining Hours", "LIVE - Air filter replaced - Engine Remaining Hours", "LIVE - Main Oil filter Remaining Hours", "LIVE - Return Oil filter Remaining Hours", "LIVE - Separator remaining", "LIVE - Motor regressed remaining", "LIVE - 1500 Valve kit Remaining Hours", "LIVE - 3000 Valve kit Remaining Hours"]:
            st.write(f"**{l_col}:** {m_data.get(l_col, '0')}")
            
    with t4:
        st.error("🚨 Next Due Dates")
        for d_col in ["OIL DUE DATE", "AFC DUE DATE", "AFE DUE DATE", "MOF DUE DATE", "ROF DUE DATE", "AOS DUE DATE", "RGT DUE DATE", "1500 KIT DUE DATE", "3000 KIT DUE DATE"]:
            st.write(f"**{d_col}:** {format_date(m_data.get(d_col))}")

    st.markdown("---")

    # 3) Service Requests
    st.subheader("🛠️ Recent Service Requests")
    svc_fab = find_col(service, ["fabrication"])
    if svc_fab:
        s_disp = service[service[svc_fab].astype(str) == str(sel_mach)].copy()
        if not s_disp.empty:
            if "Call Logged Date" in s_disp.columns: s_disp = s_disp.sort_values("Call Logged Date", ascending=False)
            for _, row in s_disp.head(5).iterrows():
                with st.expander(f"📅 {format_date(row.get('Call Logged Date'))} | {row.get('Call HMR')} | {row.get('Call Type','N/A')}"):
                    st.info(row.get("Service Engineer Comments", "No comments."))
    
    # 4) FOC Details (Mobile & Desktop Optimized with Expanders)
    st.subheader("📦 FOC Status Tracker")
    foc_fab_col = find_col(foc, ["fabrication"])
    
    if foc_fab_col:
        # Selected machine ke liye FOC filter karna
        foc_display = foc[foc[foc_fab_col].astype(str) == str(sel_mach)].copy()
        
        if not foc_display.empty:
            # Latest FOC pehle dikhane ke liye sorting
            if "Created On" in foc_display.columns:
                foc_display = foc_display.sort_values("Created On", ascending=False)
            
            for _, row in foc_display.iterrows():
                # Header labels setup
                foc_no = row.get("FOC Number", "N/A")
                foc_date = format_date(row.get("Created On"))
                # FOC Status column detect karna
                foc_status_col = find_col(foc, ["foc status", "status"])
                foc_status = row.get(foc_status_col, "In Process") if foc_status_col else "N/A"
                
                # Main Expander Label
                foc_label = f"📦 FOC: {foc_no} | 📅 {foc_date} | 🏷️ Status: {foc_status}"
                
                with st.expander(foc_label):
                    # Internal details grid layout
                    fc1, fc2 = st.columns(2)
                    with fc1:
                        st.write(f"**Work Order Number:** {row.get('Work Order Number', 'N/A')}")
                        st.write(f"**Part Code:** {row.get('Part Code', 'N/A')}")
                    with fc2:
                        st.write(f"**Failed Material Description:**")
                        st.info(row.get("Failure Material Details", "No description available."))
        else:
            st.info("Is machine ke liye koi FOC record nahi mila.")
