import streamlit as st
import pandas as pd
from io import BytesIO

# --- 1. MODERN PAGE CONFIG ---
st.set_page_config(page_title="PRIME POWER CRM Pro", layout="wide", initial_sidebar_state="expanded")

# --- 2. GLASS UI & VISIBILITY CSS ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #8b0000 0%, #dc143c 100%);
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] {
        background-color: rgba(60, 0, 0, 0.95) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
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

# --- 3. REFRESH BUTTON & HEADER ---
head_col1, head_col2 = st.columns([0.8, 0.2])
with head_col1:
    st.markdown('<h1 style="color:#ffffff; font-size:2.5rem; font-weight:800; margin-bottom:0;">PRIME POWER CRM PRO</h1>', unsafe_allow_html=True)
with head_col2:
    st.write("") 
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
st.markdown("---")

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

def format_date(val):
    if pd.isna(val) or str(val).strip() == "" or val == "N/A": return "N/A"
    try: return pd.to_datetime(val).strftime('%d-%b-%y')
    except: return str(val)

def find_col(df, kws):
    for c in df.columns:
        if any(k.lower() in str(c).lower() for k in kws): return c
    return None

cust_col = find_col(master, ["customer name", "customer"]) or "CUSTOMER NAME"
mach_col = find_col(master, ["fabrication", "fab no"]) or "FABRICATION NO."
warr_type_col = find_col(master, ["warranty type", "warranty pd"]) or "Warranty Type"
warr_exp_col = find_col(master, ["warranty expires", "warranty exp"]) or "Warranty Expires on"
comm_col = find_col(master, ["commissioning date", "comm date"]) or "Commissioning Date"

# --- SIDEBAR ---
with st.sidebar:
    log_col1, log_col2 = st.columns(2)
    try:
        with log_col1: st.image("input_file_0.png", use_container_width=True)
        with log_col2: st.image("input_file_2.png", use_container_width=True)
    except: st.warning("Logo files missing!")

    st.markdown("### 🛠️ Control Panel")
    if "Category" in master.columns:
        cat_list = ["All"] + sorted(master["Category"].dropna().unique().tolist())
        sel_cat = st.selectbox("📁 Category", cat_list)
        if sel_cat != "All": master = master[master["Category"] == sel_cat]

    sel_cust = st.selectbox("👤 Customer", ["All"] + sorted(master[cust_col].dropna().unique().tolist()))
    f_master = master.copy()
    if sel_cust != "All": f_master = master[master[cust_col] == sel_cust]
    sel_mach = st.selectbox("⚙️ Track Fabrication No.", ["All"] + sorted(f_master[mach_col].dropna().astype(str).unique().tolist()))

    st.markdown("---")
    st.markdown("### 📊 Monthly Intelligence")
    if warr_exp_col in master.columns:
        master[warr_exp_col] = pd.to_datetime(master[warr_exp_col], errors='coerce')
        if comm_col in master.columns: master[comm_col] = pd.to_datetime(master[comm_col], errors='coerce')
        
        valid_dates = master[master[warr_exp_col].notna()]
        if not valid_dates.empty:
            years = sorted(valid_dates[warr_exp_col].dt.year.unique().tolist(), reverse=True)
            sel_year = st.selectbox("Select Year", years)
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            
            w_monthly = master[master[warr_exp_col].dt.year == sel_year][warr_exp_col].dt.strftime('%B').value_counts().reindex(months).fillna(0).astype(int)
            c_monthly = pd.Series(0, index=months)
            if comm_col in master.columns:
                c_monthly = master[master[comm_col].dt.year == sel_year][comm_col].dt.strftime('%B').value_counts().reindex(months).fillna(0).astype(int)
            
            st.table(pd.DataFrame({"Comm.": c_monthly.values, "Exp.": w_monthly.values}, index=months))

# --- MAIN DASHBOARD METRICS ---
kpi_cols = st.columns(6)
kpi_cols[0].metric("👤 Customers", f_master[cust_col].nunique())
kpi_cols[1].metric("⚙️ Machines", f_master[mach_col].nunique())

if "Unit Status" in f_master.columns:
    status = f_master["Unit Status"].value_counts()
    kpi_cols[2].metric("🚚 Active", status.get("Active", 0))
    kpi_cols[3].metric("🗑️ Scraped", status.get("Scraped", 0))

if warr_type_col in f_master.columns:
    w_count = f_master[warr_type_col].nunique()
    kpi_cols[4].metric("🛡️ Warranty Types", w_count)

if warr_type_col in f_master.columns:
    st.markdown("#### 🛡️ Warranty Breakdown")
    w_breakdown = f_master[warr_type_col].value_counts()
    wb_cols = st.columns(len(w_breakdown) if len(w_breakdown) > 0 else 1)
    for i, (name, val) in enumerate(w_breakdown.items()):
        wb_cols[i % len(wb_cols)].write(f"**{name}:** `{val}`")

st.markdown("---")

# --- TRACKER & FOC LOGIC ---
foc_display = pd.DataFrame() # Initializing to avoid error

if sel_mach != "All":
    m_data = master[master[mach_col].astype(str) == str(sel_mach)].iloc[0]
    st.subheader(f"💎 Live Tracking: {sel_mach}")
    
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.write(f"**Customer:** {m_data.get('CUSTOMER NAME', 'N/A')}")
        st.write(f"**Contact:** {m_data.get('Contact No. 1', 'N/A')}")
    with t2:
        st.warning("📅 Replacements")
        for r in ["Oil R Date", "AFC R Date"]: st.write(f"**{r}:** {format_date(m_data.get(r))}")
    with t3:
        st.success("⏳ Remaining")
        st.write(f"**Oil Remaining:** {m_data.get('LIVE - Oil remaining', '0')}")
    with t4:
        st.error("🚨 Dues")
        st.write(f"**Oil Due:** {format_date(m_data.get('OIL DUE DATE'))}")

    st.markdown("---")
    # --- INSERT THIS SECTION BETWEEN LIVE TRACKING & FOC TRACKER ---
    st.markdown("---")
    st.subheader("🛠️ Recent Service Requests")
    
    # Column detection for Service file
    svc_fab = find_col(service, ["fabrication", "fab no"])
    
    if svc_fab:
        # Machine wise service history filter
        s_display = service[service[svc_fab].astype(str) == str(sel_mach)].copy()
        
        if not s_display.empty:
            # Date sorting taaki latest pehle dikhe
            if "Call Logged Date" in s_display.columns:
                s_display = s_display.sort_values("Call Logged Date", ascending=False)
            
            # Top 5 records dikhane ke liye loop
            for _, row in s_display.head(5).iterrows():
                call_date = format_date(row.get('Call Logged Date'))
                call_type = row.get('Call Type', 'Service')
                hmr = row.get('Call HMR', 'N/A')
                
                with st.expander(f"📅 {call_date} | HMR: {hmr} | Type: {call_type}"):
                    st.write(f"**Engineer:** {row.get('Service Engineer Name', 'N/A')}")
                    st.info(f"**Action Taken:** {row.get('Service Engineer Comments', 'No comments available.')}")
        else:
            st.info("Is machine ke liye koi service history available nahi hai.")
    else:
        st.error("Service sheet mein 'Fabrication' column nahi mila.")
    # FOC Details
    st.subheader("📦 FOC Status Tracker")
    foc_fab_col = find_col(foc, ["fabrication"])
    if foc_fab_col:
        foc_display = foc[foc[foc_fab_col].astype(str) == str(sel_mach)].copy()
        if not foc_display.empty:
            for _, row in foc_display.iterrows():
                with st.expander(f"📦 FOC: {row.get('FOC Number')} | Status: {row.get('Status', 'In Process')}"):
                    st.write(f"**Part:** {row.get('Part Code')}")
                    st.info(row.get("Failure Material Details", "No details."))
        else: st.info("No FOC Records.")

# --- EXPORT REPORT ---
if not foc_display.empty:
    st.markdown("---")
    st.subheader("📊 Export FOC Report")
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()
    
    st.download_button("📥 Download Excel Report", data=to_excel(foc_display), file_name="FOC_Report.xlsx")
