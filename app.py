import streamlit as st
import pandas as pd
import backend
from google import genai
import os
import base64
import time

# --- Page Configuration ---
st.set_page_config(page_title="Outreach Brain | Glassmorphism", layout="wide", page_icon="❄️")

# --- Helper function to convert local image to base64 ---
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Path to the generated background image
bg_img_path = r"C:\Users\arinc\.gemini\antigravity\brain\6dd757a7-1fa7-4167-b437-294db6a82cf0\aurora_glass_bg_1769276652775.png"
bg_img_base64 = ""
if os.path.exists(bg_img_path):
    bg_img_base64 = get_base64_of_bin_file(bg_img_path)

# --- Subtle Glassmorphism Theme (v5.6 - "The Pop" Upgrade) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;600;700;800&display=swap');

    /* Background and Global Reset */
    .stApp {{
        background: url("data:image/png;base64,{bg_img_base64}") no-repeat center center fixed;
        background-size: cover;
        color: white;
        font-family: 'Rubik', sans-serif;
    }}

    /* Higher Contrast Overlay */
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: radial-gradient(circle at center, rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0.6));
        z-index: -1;
    }}

    /* Enhanced Glass Effect */
    div[data-testid="stExpander"], .stChatMessage, .stTabs {{
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(25px) !important;
        -webkit-backdrop-filter: blur(25px) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
        margin-bottom: 2rem;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5), 
                    inset 0 0 20px rgba(255, 255, 255, 0.05) !important;
    }}

    /* Typography - Powered by Rubik */
    h1, h2, h3 {{
        font-family: 'Rubik', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 0.15em !important;
        font-weight: 400 !important;
        color: white !important;
        text-shadow: 0 0 30px rgba(255, 255, 255, 0.5), 0 0 10px rgba(14, 165, 233, 0.8) !important;
    }}

    h1 {{ font-size: 4.5rem !important; margin-bottom: 3rem !important; text-align: center; }}

    /* High-Vibrancy Pill Buttons */
    .stButton>button {{
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.3), rgba(168, 85, 247, 0.3)) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.6) !important;
        border-radius: 50px !important;
        padding: 0.9rem 3.5rem !important;
        font-family: 'Rubik', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 0.2em !important;
        font-size: 0.9rem !important;
        backdrop-filter: blur(15px);
        transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3) !important;
    }}

    .stButton>button:hover {{
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.6), rgba(168, 85, 247, 0.6)) !important;
        box-shadow: 0 0 40px rgba(14, 165, 233, 0.8), 0 0 20px rgba(168, 85, 247, 0.5) !important;
        border-color: #ffffff !important;
        transform: scale(1.05) translateY(-3px);
    }}

    /* Animated Metrics */
    [data-testid="stMetricValue"] {{
        font-family: 'Rubik', sans-serif;
        color: #ffffff !important;
        text-shadow: 0 0 15px rgba(14, 165, 233, 1), 0 0 5px rgba(255,255,255,0.5);
        font-size: 2.5rem !important;
    }}
    
    .stMetric {{
        background: rgba(255, 255, 255, 0.07);
        padding: 1.5rem;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        transition: 0.3s;
    }}
    
    .stMetric:hover {{
        border-color: #0ea5e9;
        transform: translateY(-5px);
    }}

    /* Sidebar Refinement */
    [data-testid="stSidebar"] {{
        background-color: rgba(0, 0, 0, 0.6) !important;
        backdrop-filter: blur(40px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}

    /* Input Glow */
    input, textarea, select {{
        background-color: rgba(0, 0, 0, 0.4) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        transition: 0.3s !important;
    }}
    
    input:focus, textarea:focus {{
        border-color: #0ea5e9 !important;
        box-shadow: 0 0 15px rgba(14, 165, 233, 0.4) !important;
    }}

    /* Tabs Glow Selection */
    .stTabs [data-baseweb="tab"] {{
        font-family: 'Rubik', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
    }}

    .stTabs [aria-selected="true"] {{
        color: white !important;
        border-bottom: 3px solid #0ea5e9 !important;
        text-shadow: 0 0 15px rgba(14, 165, 233, 0.8) !important;
    }}
    
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 10px rgba(14, 165, 233, 0.4); }}
        50% {{ box-shadow: 0 0 30px rgba(14, 165, 233, 0.8); }}
        100% {{ box-shadow: 0 0 10px rgba(14, 165, 233, 0.4); }}
    }}
    </style>
    """, unsafe_allow_html=True)

# --- Initialization & State ---
if 'df' not in st.session_state: 
    st.session_state.df = backend.load_vault()
if 'research_results' not in st.session_state: st.session_state.research_results = None
if 'current_prompt' not in st.session_state: st.session_state.current_prompt = ""
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'extracted_context' not in st.session_state: st.session_state.extracted_context = ""
if 'usecase' not in st.session_state: st.session_state.usecase = "BUSINESS_SALES"
if 'google_creds' not in st.session_state: st.session_state.google_creds = None

# --- Google OAuth2 Callback Handling ---
query_params = st.query_params
if "code" in query_params:
    auth_code = query_params["code"]
    # Clean up URL
    st.query_params.clear()
    
    if "google_client_config" in st.session_state:
        try:
            creds = backend.get_google_credentials(
                st.session_state.google_client_config,
                "http://localhost:8501/", # Redirect URI
                auth_code
            )
            st.session_state.google_creds = creds
            st.success("Gmail Authorization Successful!")
        except Exception as e:
            st.error(f"Authorization Failed: {e}")

# --- Sidebar ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; font-size: 1.2rem;'>Executive Panel</h2>", unsafe_allow_html=True)
    
    gemini_key = st.text_input("Access Security Key", type="password")
    
    st.divider()
    
    st.subheader("Mission Focus")
    st.session_state.usecase = st.selectbox(
        "Current Objective",
        ["BUSINESS_SALES", "JOB_HUNTING"]
    )
    
    st.divider()
    
    st.subheader("Intelligence Input")
    uploaded_files = st.file_uploader("Personnel Files / Docs", type=["pdf", "docx", "txt"], accept_multiple_files=True)
    links = st.text_area("Web Intel (Links)", placeholder="Paste URLs here...")
    
    if st.button("Index Intelligence", use_container_width=True):
        combined_text = ""
        if uploaded_files:
            for f in uploaded_files:
                combined_text += f"\n--- {f.name} ---\n" + backend.extract_text_from_file(f)
        if links:
            combined_text += f"\n--- LINKS ---\n{links}"
        st.session_state.extracted_context = combined_text
        st.success("Indexing successful.")

    st.divider()
    
    st.subheader("Communication Protocol")
    client_id = st.text_input("Google Client ID", type="password")
    client_secret = st.text_input("Google Client Secret", type="password")
    
    if client_id and client_secret:
        st.session_state.google_client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
        
        if st.session_state.google_creds is None:
            auth_url = backend.get_google_auth_url(st.session_state.google_client_config, "http://localhost:8501/")
            st.link_button("Authorize Gmail", auth_url, use_container_width=True)
        else:
            st.success("Gmail API Active")
            if st.button("Revoke Access", use_container_width=True):
                st.session_state.google_creds = None
                st.rerun()

    st.divider()
    
    # Keep legacy SMTP for fallback (optional, but requested focused on OAuth2)
    with st.expander("Legacy SMTP (Optional)"):
        gmail_user = st.text_input("Sender Address", placeholder="exec@exclusive.com")
        gmail_pass = st.text_input("Dispatch Authorization", type="password")

# --- Main App Logo / Hero ---
st.markdown("<h1>OUTREACH BRAIN</h1>", unsafe_allow_html=True)

# Quick Metrics Bar (Symmetrical Glass Cards)
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1: st.metric("VAULT NODES", len(st.session_state.df) if st.session_state.df is not None else 0)
with m_col2: st.metric("INTEL CAPACITY", f"{len(st.session_state.extracted_context)} chars")
with m_col3: st.metric("PROTOCOL", st.session_state.usecase.upper())

st.markdown("<br>", unsafe_allow_html=True)

# --- Primary Tabs ---
tab_finder, tab_strategist, tab_vault, tab_neural, tab_launch, tab_analytics = st.tabs([
    "Lead Prospecting", 
    "AI Strategy",
    "Intelligence Vault", 
    "Neural Drafting", 
    "Mission Launch",
    "📊 Campaign Analytics"
])

# --- Tab 0: Intel Finder ---
with tab_finder:
    st.subheader("Global Prospecting")
    search_query = st.text_input("Mission Sector", placeholder="e.g., Venture Capitalists in Gurgaon")
    
    if st.button("Execute Global Research", use_container_width=True):
        if not gemini_key: 
            st.error("Security Key Required.")
        elif not search_query:
            st.warning("Please specify a Mission Sector.")
        else:
            with st.spinner("Automating Research Protocol & Accessing Web Intel..."):
                try:
                    # Logic is now internal: Generate -> Execute
                    final_prompt = backend.generate_search_prompt(search_query)
                    res = backend.search_and_extract_leads(search_query, gemini_key, st.session_state.usecase, final_prompt)
                    st.session_state.research_results = res
                    st.success(f"Acquired {len(res)} intelligence nodes.")
                except Exception as e:
                    st.error(f"Interference detected: {e}")

    if st.session_state.research_results is not None:
        st.dataframe(st.session_state.research_results, use_container_width=True)
        if st.button("Secure to Vault"):
            if st.session_state.df is None:
                st.session_state.df = st.session_state.research_results
            else:
                st.session_state.df = pd.concat([st.session_state.df, st.session_state.research_results]).drop_duplicates(subset=['id', 'contact_email', 'name'])
            backend.save_vault(st.session_state.df)
            st.success("Nodes secured and persisted.")

# --- Tab 1: AI Strategist ---
with tab_strategist:
    st.subheader("Strategic Consultation")
    st.markdown("<p style='color: rgba(255,255,255,0.6);'>Interact with the AI to refine your mission parameters.</p>", unsafe_allow_html=True)
    
    for msg in st.session_state.chat_history:
        role = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input("Enter strategic query..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            if not gemini_key:
                response = "Access Denied: Secure your API link."
            else:
                client = genai.Client(api_key=gemini_key)
                gemini_history = []
                for m in st.session_state.chat_history:
                    role = "user" if m["role"] == "user" else "model"
                    gemini_history.append({"role": role, "parts": [{"text": m["content"]}]})
                
                response = backend.get_strategist_response(client, gemini_history, st.session_state.extracted_context)
            st.markdown(response)
            st.session_state.chat_history.append({"role": "model", "content": response})

# --- Tab 2: Intel Vault ---
with tab_vault:
    st.subheader("Personnel Master Index")
    if st.session_state.df is not None:
        st.dataframe(st.session_state.df, use_container_width=True)
        v_col1, v_col2 = st.columns([1, 1])
        with v_col1:
            if st.button("FILL INTELLIGENCE (AUTO-ENRICH)", use_container_width=True):
                if not gemini_key:
                    st.error("Authorization Required to use Brain.")
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    if st.session_state.df is not None:
                        # STANDARDIZE: Convert all missing/NaN to '0' so the AI sees them clearly
                        target_cols = ["website", "contact_email", "phone", "address"]
                        for col in target_cols:
                            st.session_state.df[col] = st.session_state.df[col].fillna("0")
                            st.session_state.df.loc[st.session_state.df[col] == "", col] = "0"

                        # Identify rows where ANY field is '0' (missing) or '[NOT_FOUND]' (retryable)
                        mask = st.session_state.df[target_cols].apply(lambda x: x.map(backend.is_missing)).any(axis=1)
                        rows_to_fill = st.session_state.df[mask]
                        total = len(rows_to_fill)
                        
                        if total == 0:
                            st.info("Intelligence already saturated. No empty nodes found.")
                        else:
                            success_count = 0
                            for i, (index, row) in enumerate(rows_to_fill.iterrows()):
                                status_text.text(f"Enriching Node: {row['name']} at {row['company']} ({i+1}/{total})")
                                
                                # Use to_dict() for AI payload
                                row_dict = row.to_dict()
                                new_info = backend.fill_missing_info(row_dict, gemini_key)
                                
                                if new_info:
                                    found_fields = [f for f, v in new_info.items() if v and not backend.is_missing(v)]
                                    if found_fields:
                                        success_count += 1
                                        st.toast(f"✅ Found {', '.join(found_fields)} for {row['name']}")
                                        for field, value in new_info.items():
                                            if value and not backend.is_missing(value):
                                                st.session_state.df.at[index, field] = value
                                            else:
                                                # If AI still couldn't find it, mark as [NOT_FOUND]
                                                st.session_state.df.at[index, field] = "[NOT_FOUND]"
                                        
                                        backend.save_vault(st.session_state.df)
                                    else:
                                        st.toast(f"⚠️ No new intel found for {row['name']}", icon="🔍")
                                        # Mark all missing fields as [NOT_FOUND] for this failed attempt
                                        for field in [f for f in target_cols if backend.is_missing(row.get(f))]:
                                            st.session_state.df.at[index, field] = "[NOT_FOUND]"
                                        backend.save_vault(st.session_state.df)
                                
                                progress_bar.progress((i + 1) / total)
                            
                            status_text.success(f"Intelligence saturation complete. {success_count} nodes updated.")
                            st.rerun()
                            
                            status_text.success(f"Intelligence saturation complete. {success_count} nodes updated.")
                            st.rerun()
        
        with v_col2:
            if st.button("Wipe Vault Memory", use_container_width=True):
                st.session_state.df = None
                import os
                if os.path.exists("vault.csv"): os.remove("vault.csv")
                st.rerun()
    else:
        st.info("Vault is zeroed. Populate via Lead Finder or legacy CSV.")
        
    ext_file = st.file_uploader("Input External Datasets (CSV)", type="csv")
    if ext_file:
        new_leads = backend.process_upload(ext_file, mode=st.session_state.usecase)
        if st.session_state.df is None:
            st.session_state.df = new_leads
        else:
            st.session_state.df = pd.concat([st.session_state.df, new_leads]).drop_duplicates(subset=['id', 'contact_email', 'name'])
        backend.save_vault(st.session_state.df)
        st.success("Datasets integrated and persisted.")

# --- Tab 3: Neural Drafting ---
with tab_neural:
    st.subheader("Synthesizing Communications")
    if st.session_state.df is None:
        st.warning("Intelligence Vault Empty.")
    else:
        preset = st.selectbox("Neural Preset", ["Bespoke Email", "LinkedIn Protocol", "Letter of Intent", "Follow-up"])
        
        if st.button("Execute Neural Synthesis"):
            if not gemini_key: st.error("Authorization Required.")
            else:
                with st.spinner("Processing neural patterns..."):
                    full_ctx = f"USECASE: {st.session_state.usecase}\nPRESET: {preset}\nMISSION INTEL: {st.session_state.extracted_context}\n"
                    st.session_state.df = backend.generate_email_drafts(st.session_state.df, gemini_key, full_ctx)
                    backend.save_vault(st.session_state.df)
                    st.success("Synthesis stable and persisted.")
        
        if "draft_body" in st.session_state.df.columns:
            st.data_editor(st.session_state.df, use_container_width=True)

# --- Tab 4: Mission Launch ---
with tab_launch:
    st.subheader("Tactical Dispatch")
    if st.session_state.df is None or "draft_body" not in st.session_state.df.columns:
        st.warning("Finalize Drafts Prior to Dispatch.")
    else:
        st.write(f"ACTIVE NODES: {len(st.session_state.df)}")
        if st.button("INITIATE GLOBAL DISPATCH", use_container_width=True):
            if st.session_state.google_creds:
                with st.spinner("Broadcasting mission content via Gmail API..."):
                    try:
                        results = backend.send_batch_emails_api(st.session_state.df, st.session_state.google_creds)
                        backend.save_vault(st.session_state.df)
                        st.success(f"DISPATCH LOG: {results['sent']} SENT | {results['failed']} FAILED")
                    except Exception as e:
                        st.error(f"Gmail API Error: {str(e)}")
            elif gmail_user and gmail_pass:
                with st.spinner("Broadcasting mission content via SMTP..."):
                    try:
                        results = backend.send_batch_emails(st.session_state.df, gmail_user, gmail_pass)
                        backend.save_vault(st.session_state.df)
                        st.success(f"DISPATCH LOG: {results['sent']} SENT | {results['failed']} FAILED")
                    except Exception as e:
                        st.error(f"Dispatch Error: {str(e)}")
                        if "Authentication Failed" in str(e):
                            st.info("💡 **Quick Fix:** Go to Google Account Settings > Security > 2-Step Verification > App Passwords. Generate a 16-character code and paste it into the 'Dispatch Authorization' field.")
            else:
                st.error("Authentication Missing. Please authorize Gmail or provide SMTP credentials.")

        with st.expander("🛠️ Authentication Guide"):
            st.markdown("""
            **Option A: Google API (Recommended)**
            1. Create a project in [Google Cloud Console](https://console.cloud.google.com/).
            2. Enable 'Gmail API'.
            3. Create OAuth Client ID (Web Application).
            4. Set Redirect URI to `http://localhost:8501/`.
            5. Copy Client ID and Secret to the sidebar.

            **Option B: Legacy SMTP**
            1. Enable 2-Step Verification on your Google Account.
            2. Generate an [App Password](https://myaccount.google.com/apppasswords).
            3. Paste it into the 'Legacy SMTP' section.
            """)

# --- Tab 5: Campaign Analytics ---
with tab_analytics:
    st.subheader("Mission Performance Matrix")
    if st.session_state.df is None:
        st.info("No active operations found in vault.")
    else:
        total = len(st.session_state.df)
        with_email = len(st.session_state.df[st.session_state.df["contact_email"] != ""])
        with_draft = len(st.session_state.df[st.session_state.df["draft_status"] == "GENERATED"])
        sent = len(st.session_state.df[st.session_state.df["send_status"] == "SENT"])
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("TOTAL NODES", total)
        col2.metric("INTEL SATURATION", f"{(with_email/total*100):.1f}%" if total > 0 else "0%")
        col3.metric("DRAFTING PROGRESS", f"{(with_draft/total*100):.1f}%" if total > 0 else "0%")
        col4.metric("DISPATCH SUCCESS", f"{(sent/total*100):.1f}%" if total > 0 else "0%")
        
        st.divider()
        st.markdown("### Resource Allocation Over Time")
        # Simple placeholder for visual balance
        st.line_chart(st.session_state.df["draft_status"].value_counts())

st.divider()
st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.4); font-size: 0.7rem;'>VERSION 5.5 | SUBTLE GLASSMORPHISM OPERATING SYSTEM</p>", unsafe_allow_html=True)
