# =============== INDUSTRIAL TRACKER PRO (UPDATED) =============== #
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from io import BytesIO
import requests

st.set_page_config(layout="wide", page_title="Industrial Dashboard")

# ================= 1. CLOUD SYNC SETUP =================
# ⚠️ Apne naye Merged Excel file ka link yahan dalein jisme 4 sheets hon: Master, FOC, Service, AMC
merged_url = "https://api.onedrive.com/v1.0/shares/u!Aapka_Naya_Merged_Link_Yahan/root/content?download=1"

@st.cache_data(ttl=60)
def load_merged_cloud_data():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(merged_url, headers=headers, allow_redirects=True, timeout=30)
        
        if response.status_code == 200:
            file_bytes = BytesIO(response.content)
            with pd.ExcelFile(file_bytes, engine='openpyxl') as xls:
                # 4 Sheets load karna
                m = pd.read_excel(xls, sheet_name='Master').fillna("")
                f = pd.read_excel(xls, sheet_name='FOC').fillna("")
                s = pd.read_excel(xls, sheet_name='Service').fillna("")
                a = pd.read_excel(xls, sheet_name='AMC').fillna("")
            return m, f, s, a
        else:
            return None, None, None, None
    except Exception as e:
        return None, None, None, None

# Load data
df, foc, service, amc_df = load_merged_cloud_data()

# ================= 2. LOCAL BACKUP (Agar Cloud Fail ho) =================
if df is None or df.empty:
    st.sidebar.warning("⚠️ Cloud Sync failed. Using local files.")
    df = pd.read_excel("Master_OD_Data.xlsx").fillna("")
    foc = pd.read_excel("Active_FOC.xlsx").fillna("")
    service = pd.read_excel("Service_Details.xlsx").fillna("")
    try:
        amc_df = pd.read_excel("AMC_Details.xlsx").fillna("")
    except:
        amc_df = pd.DataFrame()
        st.sidebar.warning("AMC file not loaded")

# Clean Column Names
for dataframe in [df, foc, service, amc_df]:
    if not dataframe.empty:
        dataframe.columns = dataframe.columns.str.strip()

# ================= 3. PREMIUM GLASS CSS =================
st.markdown("""
<style>
/* ---------- GLOBAL DARK MODE ---------- */
html, body, [class*="css"]  {
    background-color: #0f172a;
    color: #e2e8f0;
}
/* ---------- SIDEBAR ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617, #0f172a);
    border-right: 1px solid rgba(255,255,255,0.05);
}
/* ---------- GLASS CARD ---------- */
.glass-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 20px;
    border: 1px solid rgba(255,255,255,0.1);
    transition: 0.3s ease;
}
.glass-card:hover {
    transform: translateY(-5px) scale(1.01);
    box-shadow: 0px 10px 30px rgba(0,0,0,0.4);
}
/* ---------- BUTTON ---------- */
.stButton>button {
    border-radius: 10px;
    background: linear-gradient(90deg, #2563eb, #06b6d4);
    color: white;
    border: none;
}
/* ---------- SCROLLBAR ---------- */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# ================= HELPER FUNCTIONS =================
def fmt_date(val):
    try:
        dt = pd.to_datetime(val, errors='coerce')
        if pd.isna(dt): return ""
        return dt.strftime("%d-%b-%y")
    except:
        return str(val)

def get_col(data_f, keyword):
    return next((c for c in data_f.columns if keyword.lower() in c.lower()), None)

# Dynamic Column Matching
cust_col = get_col(df, "customer")
fab_col = get_col(df, "fabrication")
connect_col = get_col(df, "connect_status")
cat_col = get_col(df, "sub category")
w_col = get_col(df, "warranty")
amc_col = get_col(df, "amc")
overdue_col = get_col(df,"over due")
curr_col   = get_col(df,"current month due")
next_col   = get_col(df,"next month due")

# ================= SIDEBAR FILTERS & REFRESH =================
st.title("🏭 Industrial Dashboard")
if st.sidebar.button("🔄 Sync Online Data"):
    st.cache_data.clear()
    st.rerun()

df[cust_col] = df[cust_col].astype(str)
customers = ["All"] + sorted(df[cust_col].unique())
sel = st.sidebar.selectbox("Customer Filter", customers)
df_f = df if sel == "All" else df[df[cust_col] == sel]

# ================= KPI COUNTS =================
def count_flag(series):
    s = series.astype(str).str.strip().str.lower()
    return s.isin(["1", "1.0", "yes", "y", "true"]).sum()

overdue_count = count_flag(df_f[overdue_col]) if overdue_col else 0
current_month_count = count_flag(df_f[curr_col]) if curr_col else 0
next_month_count = count_flag(df_f[next_col]) if next_col else 0

if overdue_count > 0:
    st.error(f"⚠️ {overdue_count} Overdue Units Need Attention")
else:
    st.success("✔️ No overdue units")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Units", len(df_f))
col2.metric("Overdue", overdue_count)
col3.metric("Current Month Due", current_month_count)
col4.metric("Next Month Due", next_month_count)

# ================= NEW: SERVICE URGENCY TRACKER (RADIO BUTTONS) =================
st.markdown("---")
st.header("🚨 Live Service Urgency Tracker")

selected_status = st.radio(
    "Urgency Status Chunein:",
    options=["⚠️ Over Due Machines", "📅 Current Month Due", "⏭️ Next Month Due"],
    horizontal=True
)

status_mapping = {
    "⚠️ Over Due Machines": overdue_col,
    "📅 Current Month Due": curr_col,
    "⏭️ Next Month Due": next_col
}
target_status_col = status_mapping[selected_status]

# Standard columns for display
display_hint_cols = ["fabrication", "model", "customer", "location", "hmr"]
disp_cols = [get_col(df, h) for h in display_hint_cols if get_col(df, h)]

if target_status_col:
    # Filter based on flag (1, yes, etc)
    flag_mask = df_f[target_status_col].astype(str).str.strip().str.lower().isin(["1", "1.0", "yes", "y", "true"])
    filtered_status_df = df_f[flag_mask].copy()

    if not filtered_status_df.empty:
        st.write(f"🔍 **Total {len(filtered_status_df)} units** in **{selected_status}**")
        st.dataframe(filtered_status_df[disp_cols + [target_status_col]], use_container_width=True, hide_index=True)
        
        st.download_button(
            label=f"📥 Download {selected_status} (CSV)",
            data=filtered_status_df.to_csv(index=False).encode('utf-8'),
            file_name=f"{selected_status[:5]}_list.csv",
            mime='text/csv'
        )
    else:
        st.info(f"👍 No machines pending in **{selected_status}** category.")

# ================= NEW: PARTS DUE PLANNER (MULTISELECT) =================
st.markdown("---")
st.header("🛠️ Preventative Maintenance Planner")

# Dynamic Part Mapping based on Industrial DB
part_mapping_raw = {
    'Air Filter (AF)': get_col(df, 'AF DUE DATE'),
    'Oil Filter (OF)': get_col(df, 'OF DUE DATE'),
    'Compressor Oil (OIL)': get_col(df, 'OIL DUE DATE'),
    'Separator (AOS)': get_col(df, 'AOS DUE DATE'),
    'Valve Kit (VK)': get_col(df, 'VALVEKIT DUE DATE'),
    'Regulator (RGT)': get_col(df, 'RGT DUE DATE')
}
part_mapping = {k: v for k, v in part_mapping_raw.items() if v} # Remove Nones

if part_mapping:
    selected_parts = st.multiselect(
        "Select Parts to check Due Schedule:",
        options=list(part_mapping.keys()),
        default=[list(part_mapping.keys())[0]]
    )

    if selected_parts:
        planner_df = df_f.copy()
        date_cols = [part_mapping[p] for p in selected_parts]
        
        for col in date_cols:
            planner_df[col] = pd.to_datetime(planner_df[col], errors='coerce')
            
        primary_col = part_mapping[selected_parts[0]]
        planner_df = planner_df.dropna(subset=[primary_col])

        if not planner_df.empty:
            planner_df['Year'] = planner_df[primary_col].dt.year.astype(int)
            planner_df['Month'] = planner_df[primary_col].dt.strftime('%B')

            f_col1, f_col2 = st.columns(2)
            with f_col1:
                sel_year = st.selectbox("Select Year", sorted(planner_df['Year'].unique()))
            with f_col2:
                sel_month = st.selectbox("Select Month", planner_df[planner_df['Year'] == sel_year]['Month'].unique())

            final_table = planner_df[(planner_df['Year'] == sel_year) & (planner_df['Month'] == sel_month)].copy()
            
            for col in date_cols:
                final_table[col] = pd.to_datetime(final_table[col]).dt.strftime('%d-%b-%y')

            st.write(f"🔍 **{len(final_table)} units** due in **{sel_month} {sel_year}**")
            st.dataframe(final_table[disp_cols + date_cols], use_container_width=True, hide_index=True)
            
            st.download_button(
                label="📥 Download Parts Due List",
                data=final_table.to_csv(index=False).encode('utf-8'),
                file_name=f"Parts_Due_{sel_month}_{sel_year}.csv",
                mime='text/csv'
            )
        else:
            st.info("No records found for the selected timeline.")

# ================= SMART SEARCH =================
st.markdown("---")
st.subheader("🔎 Smart Search")
search = st.text_input("Search by Fabrication / Customer / Model")

if search:
    result = df_f[df_f.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)]
    if not result.empty:
        st.dataframe(result.head(20), use_container_width=True)
    else:
        st.warning("No matching record found")

# ================= MACHINE TRACKER (Fixed Indentation) =================
st.markdown("---")
st.subheader("🔍 Machine Tracker")

machines = ["Select"] + list(df_f[fab_col].astype(str).unique())
sel_f = st.selectbox("Select Machine for Deep Dive", machines, key="main_machine_tracker")

if sel_f != "Select":
    # --- Service History ---
    st.markdown("### 📜 Service History")
    fab_col_service = get_col(service, "fabrication")
    svc_df = service[service[fab_col_service].astype(str) == str(sel_f)] if fab_col_service else pd.DataFrame()

    if not svc_df.empty:
        for i, r_s in svc_df.iterrows():
            with st.expander(f"📅 {fmt_date(r_s.get('Call Logged Date'))} | {r_s.get('Call Type','-')}"):
                st.write(f"**Call HMR:** {r_s.get('Call HMR','-')}")
                st.write(f"**Comment:** {r_s.get('Service Engineer Comment','-')}")
    else:
        st.info("No Service History Found")

    # --- Customer & Machine Details ---
    row = df_f[df_f[fab_col].astype(str) == str(sel_f)].iloc[0]
    
    st.download_button("⬇ Download Machine Report", pd.DataFrame([row]).to_csv(index=False), file_name=f"{sel_f}_Report.csv", mime="text/csv")
    
    def pick(h):
        c = get_col(df,h)
        return row.get(c,"-") if c else "-"

    a,b,c,d = st.columns(4)
    with a:
        st.markdown("### 👤 Info")
        st.write(f"**Cust:** {pick('customer')}")
        st.write(f"**Model:** {pick('model')}")
        st.write(f"**Loc:** {pick('location')}")
    with b:
        st.markdown("### 🔧 Replacements")
        for p in ["AF R Date","OF R Date","Oil R Date","AOS R Date","RGT R Date","Valvekit R Date"]:
            st.write(f"{p[:5]}: {fmt_date(pick(p))}")
    with c:
        st.markdown("### ⏳ Rem. Hours")
        for p in ["AF Rem","OF Rem","OIL Rem","AOS Rem","VK Rem"]:
            try:
                hrs = float(pick(p))
                if hrs < 0: st.error(f"{p[:3]}: {hrs}")
                else: st.success(f"{p[:3]}: {hrs}")
            except:
                st.write(f"{p[:3]}: -")
    with d:
        st.markdown("### 📅 Due Dates")
        for p in ["AF DUE DATE","OF DUE DATE","OIL DUE DATE","AOS DUE DATE","VALVEKIT DUE DATE"]:
            try:
                due_dt = pd.to_datetime(pick(p))
                if due_dt < pd.Timestamp.today(): st.error(f"{p[:3]}: {fmt_date(due_dt)}")
                else: st.success(f"{p[:3]}: {fmt_date(due_dt)}")
            except:
                st.write(f"{p[:3]}: -")

    # --- FOC Details ---
    st.markdown("### 📦 FOC Details")
    fab_col_foc = get_col(foc, "fabrication")
    foc_df = foc[foc[fab_col_foc].astype(str) == str(sel_f)] if fab_col_foc else pd.DataFrame()
    if not foc_df.empty:
        st.dataframe(foc_df, use_container_width=True)
    else:
        st.info("No FOC Data Found")

# ================= SIDEBAR WIDGETS =================
if connect_col:
    st.sidebar.subheader("📊 Unit Status")
    st.sidebar.write(df_f[connect_col].value_counts())

# AMC Tracking (Sidebar)
st.sidebar.subheader("📆 AMC Status Summary")
amc_status_col = get_col(df, "amc status")
if amc_status_col:
    counts = df[amc_status_col].value_counts()
    st.sidebar.write(counts)
