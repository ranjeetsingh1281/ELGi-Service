import streamlit as st
from supabase import create_client, Client

# ==============================
# 🔐 CLOUD CONFIG
# ==============================
st.set_page_config(page_title="ELGi Cloud Link", layout="centered")

if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
    URL = st.secrets["SUPABASE_URL"].strip()
    KEY = st.secrets["SUPABASE_KEY"].strip()
    
    try:
        # Client initialize karna
        supabase: Client = create_client(URL, KEY)
        st.success("✅ Supabase Client Initialized!")
    except Exception as e:
        st.error(f"❌ Connection Failed: {e}")
        st.stop()
else:
    st.warning("🚨 Streamlit Secrets Khali Hain! Please fill URL and KEY in Settings.")
    st.stop()

# ==============================
# 🔍 THE BIG TEST
# ==============================
st.title("🛡️ Connection Status")

if st.button("🚀 Check Real-Time Link"):
    try:
        # Testing machine table
        res = supabase.table("machines").select("count", count="exact").limit(1).execute()
        st.balloons()
        st.success(f"🔥 BINGO BOSS! Database Connected! Found {res.count} machines.")
    except Exception as e:
        st.error(f"❌ DB Response Error: {e}")
        st.info("💡 Tip: Ensure the 'anon' key is copied fully from the API Keys tab.")
