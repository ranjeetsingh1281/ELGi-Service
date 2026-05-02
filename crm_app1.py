import streamlit as st
import pandas as pd
from io import BytesIO

# --- 1. MOBILE-FRIENDLY PAGE CONFIG ---
# Layout ko "centered" rakha hai taaki mobile par horizontal scrolling na ho
st.set_page_config(page_title="PRIME POWER Mobile CRM", layout="centered", initial_sidebar_state="collapsed")

# --- FINAL VISIBILITY FIX FOR MOBILE CRIMSON UI ---
st.markdown("""
    <style>
    /* 1. Global Text Force White */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #8b0000 0%, #dc143c 100%);
    }
    
    /* Force ALL text to be white/bright light grey */
    h1, h2, h3, h4, p, span, label, li {
        color: #ffffff !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5); /* Shadow for better depth */
    }

    /* 2. Metric Cards Visibility Fix */
    div[data-testid="stMetricValue"] > div {
        color: #00ffff !important; /* Bright Cyan for Numbers - High Contrast */
        font-weight: 800 !important;
        font-size: 2.2rem !important;
    }
    
    div[data-testid="stMetricLabel"] > div > p {
        color: #f8fafc !important; /* Off-white for labels */
        font-size: 1rem !important;
        font-weight: 600 !important;
    }

    /* 3. Sidebar Visibility Fix */
    [data-testid="stSidebar"] label p {
        color: #ffffff !important;
    }
    
    /* 4. Info/Success/Warning Box Text Fix */
    .stAlert p {
        color: #ffffff !important;
        font-weight: 500;
    }

    /* 5. Selectbox Input Fix (Inside white boxes) */
    [data-testid="stSidebar"] div[data-baseweb="select"] div {
        color: #000000 !important; /* Dark text inside white input boxes */
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
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

master, service, foc = load_data()

# Clean & Detect Columns
for df in [master, service, foc]:
    if not df.empty: df.columns = df.columns.str.strip()

def find_col(df, kws):
    for c in df.columns:
        if any(k.lower() in str(c).lower() for k in kws): return c
    return None

cust_col = find_col(master, ["customer name", "customer"]) or "CUSTOMER NAME"
mach_col = find_col(master, ["fabrication", "fab no"]) or "FABRICATION NO."
warr_exp_col = find_col(master, ["warranty expires", "warranty exp"]) or "Warranty Expires on"

# --- SIDEBAR WITH LOGOS ---
with st.sidebar:
    log_col1, log_col2 = st.columns(2)
    try:
        with log_col1: st.image("input_file_1.png", use_container_width=True)
        with log_col2: st.image("input_file_0.png", use_container_width=True)
    except: st.write("🏷️ **PRIME POWER | ELGi**")
    
    st.markdown("### 🛠️ Control Panel")
    sel_cust = st.selectbox("👤 Customer", ["All"] + sorted(master[cust_col].dropna().unique().tolist()))
    
    f_master = master.copy()
    if sel_cust != "All": f_master = master[master[cust_col] == sel_cust]
    
    sel_mach = st.selectbox("⚙️ Track Fab No.", ["All"] + sorted(f_master[mach_col].dropna().astype(str).unique().tolist()))

    # Warranty Table (Collapsed by default on mobile)
    with st.expander("📅 Warranty Tracker"):
        if warr_exp_col in master.columns:
            master[warr_exp_col] = pd.to_datetime(master[warr_exp_col], errors='coerce')
            valid_dates = master[master[warr_exp_col].notna()]
            years = sorted(valid_dates[warr_exp_col].dt.year.unique().tolist(), reverse=True)
            sel_year = st.selectbox("Year", years)
            monthly = valid_dates[valid_dates[warr_exp_col].dt.year == sel_year][warr_exp_col].dt.strftime('%B').value_counts()
            st.write(monthly)

# --- MAIN DASHBOARD (MOBILE READY) ---
st.markdown('<h1>PRIME POWER CRM MOBILE</h1>', unsafe_allow_html=True)

# Metrics - Ek row mein 2 (Mobile par stacked dikhenge)
m1, m2 = st.columns(2)
m1.metric("👤 Customers", f_master[cust_col].nunique())
m2.metric("⚙️ Machines", f_master[mach_col].nunique())

if "Unit Status" in f_master.columns:
    status = f_master["Unit Status"].value_counts()
    s1, s2 = st.columns(2)
    s1.metric("🚚 Active", status.get("Active", 0))
    s2.metric("❌ Sold", status.get("Sold", 0))

st.markdown("---")

# 4-Column Tracker (Mobile par stack ho jayega)
if sel_mach != "All":
    m_data = master[master[mach_col].astype(str) == str(sel_mach)].iloc[0]
    st.subheader(f"💎 Tracking: {sel_mach}")
    
    # Customer Info Box
    st.markdown('<div style="background:rgba(255,255,255,0.1); padding:15px; border-radius:10px; border-left:5px solid #38bdf8; margin-bottom:10px;">'
                f'<b>👤 Customer:</b> {m_data.get("CUSTOMER NAME","N/A")}<br>'
                f'<b>📞 Contact:</b> {m_data.get("Contact No. 1","N/A")}</div>', unsafe_allow_html=True)

    # Replacement Info Box
    st.markdown('<div style="background:rgba(255,255,255,0.1); padding:15px; border-radius:10px; border-left:5px solid #fbbf24; margin-bottom:10px;">'
                f'<b>📅 Oil R Date:</b> {m_data.get("Oil R Date","N/A")}<br>'
                f'<b>📅 AFC R Date:</b> {m_data.get("AFC R Date","N/A")}</div>', unsafe_allow_html=True)

    # Service & FOC in Expanders (Best for mobile)
    with st.expander("🛠️ Recent Service History"):
        svc_fab = find_col(service, ["fabrication"])
        if svc_fab:
            s_disp = service[service[svc_fab].astype(str) == str(sel_mach)].head(5)
            st.dataframe(s_disp)

    with st.expander("📦 FOC Details"):
        foc_fab = find_col(foc, ["fabrication"])
        if foc_fab:
            f_disp = foc[foc[foc_fab].astype(str) == str(sel_mach)]
            st.dataframe(f_disp)
else:
    st.info("📱 Sidebar se machine select karein.")
