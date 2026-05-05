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

# --- 1) Metrics & Charts Section (Indentation Fixed) ---
if sel_mach == "All":
    # Top Row Metrics
    kpi_cols = st.columns(4)
    kpi_cols[0].metric("👤 Total Customers", f_master[cust_col].nunique())
    kpi_cols[1].metric("⚙️ Total Machines", f_master[mach_col].nunique())
    
    if "Unit Status" in f_master.columns:
        status_map = f_master["Unit Status"].value_counts()
        kpi_cols[2].metric("🚚 Active", status_map.get("Active", 0))
    
    if warr_type_col in f_master.columns:
        w_count = f_master[warr_type_col].nunique()
        kpi_cols[3].metric("🛡️ Warranty Types", w_count)

    st.markdown("---")

    # --- CHARTS SECTION (Side-by-Side) ---
    c_col1, c_col2 = st.columns(2)

    with c_col1:
        st.subheader("📊 Warranty vs Non-Warranty")
        if warr_type_col in f_master.columns:
            # Logic: Categorize into Warranty vs Non-Warranty
            f_master['W_Status'] = f_master[warr_type_col].apply(
                lambda x: "Non-Warranty" if str(x).lower() in ["non-warranty", "nan", "out of warranty"] else "Warranty"
            )
            w_data = f_master['W_Status'].value_counts().reset_index()
            w_data.columns = ['Status', 'Count']
            
            fig_bar = px.bar(w_data, x='Status', y='Count', color='Status',
                             color_discrete_map={'Warranty': '#00C851', 'Non-Warranty': '#ff4444'},
                             text_auto=True)
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", height=350)
            st.plotly_chart(fig_bar, use_container_width=True)

    with c_col2:
        st.subheader("⭕ Expiry Analysis")
        if warr_exp_col in f_master.columns:
            today = datetime.now()
            f_master[warr_exp_col] = pd.to_datetime(f_master[warr_exp_col], errors='coerce')
            
            # Count logic for Pie Chart
            od = f_master[f_master[warr_exp_col] < today].shape[0]
            curr_m = f_master[(f_master[warr_exp_col].dt.month == today.month) & (f_master[warr_exp_col].dt.year == today.year)].shape[0]
            
            next_m_val = (today.month % 12) + 1
            next_m_yr = today.year + (1 if today.month == 12 else 0)
            nxt_m = f_master[(f_master[warr_exp_col].dt.month == next_m_val) & (f_master[warr_exp_col].dt.year == next_m_yr)].shape[0]
            
            pie_df = pd.DataFrame({
                "Category": ["Overdue", "Current Month Due", "Next Month Due"],
                "Count": [od, curr_m, nxt_m]
            })
            
            fig_pie = px.pie(pie_df, values='Count', names='Category', 
                             color_discrete_sequence=['#ff4444', '#ffbb33', '#0099CC'],
                             hole=0.4)
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", height=350)
            st.plotly_chart(fig_pie, use_container_width=True)

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
        
    st.markdown("---")
  
    # FOC Details
   # --- FIXED FOC TRACKER (GROUPED BY FOC NUMBER) ---
    st.subheader("📦 FOC Status Tracker")
    foc_fab_col = find_col(foc, ["fabrication", "fab no"])
    
    if foc_fab_col:
        f_display = foc[foc[foc_fab_col].astype(str) == str(sel_mach)].copy()
        
        if not f_display.empty:
            # FOC Number ke hisaab se group banana taaki duplicate headers na dikhein
            grouped = f_display.groupby("FOC Number")
            
            # Latest FOC pehle dikhane ke liye (Based on first entry of group)
            sorted_groups = sorted(grouped, key=lambda x: str(x[1]["Created On"].iloc[0]) if "Created On" in x[1].columns else "", reverse=True)

            for foc_no, group_df in sorted_groups:
                first_row = group_df.iloc[0]
                f_date = format_date(first_row.get("Created On"))
                f_status_col = find_col(foc, ["foc status", "status"])
                f_status = first_row.get(f_status_col, "In Process") if f_status_col else "N/A"
                
                # Header mein sirf ek baar FOC Details dikhegi
                with st.expander(f"📦 FOC: {foc_no} | 📅 {f_date} | 🏷️ Status: {f_status}"):
                    st.write(f"**Work Order:** {first_row.get('Work Order Number', 'N/A')}")
                    st.markdown("---")
                    # Group ke andar ke saare parts ki list
                    for _, row in group_df.iterrows():
                        st.write(f"🔹 **Part:** {row.get('Part Code', 'N/A')} | **Qty:** {row.get('Qty', '1')}")
                        st.caption(f"Details: {row.get('Failure Material Details', 'No description')}")
                        st.markdown("---")
        else:
            st.info("Is machine ke liye koi FOC record nahi mila.")

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
