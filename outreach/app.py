import streamlit as st
import pandas as pd
import backend
from google import genai
import os
import base64
import time

# --- Page Configuration ---
st.set_page_config(page_title="Outreach Brain | Viewport Lock 2.0", layout="wide", page_icon="❄️")

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

# --- v6.7 UI Styling ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    :root {{
        --background: 240 10% 3.9%;
        --foreground: 0 0% 98%;
        --card: 240 10% 4.9%;
        --border: 240 3.7% 15.9%;
        --radius: 0.75rem;
    }}

    .stApp {{
        background: url("data:image/png;base64,{bg_img_base64}") no-repeat center center fixed;
        background-size: cover;
        font-family: 'Inter', sans-serif;
    }}

    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(9, 9, 11, 0.8);
        z-index: -1;
    }}

    /* Component A: Sticky Secondary Navigation */
    div[data-testid="stTabs"] {{
        position: sticky !important;
        top: 0 !important;
        background: rgba(9, 9, 11, 0.8) !important;
        backdrop-filter: blur(10px) !important;
        z-index: 50 !important;
        border-bottom: 1px solid rgba(82, 82, 82, 0.2) !important;
        padding: 0.5rem 1rem !important;
        border-radius: var(--radius) !important;
    }}

    /* Component B: Flex-Column Chat Container */
    .chat-viewport-strict {{
        height: calc(100vh - 250px) !important;
        display: flex !important;
        flex-direction: column !important;
        overflow: hidden !important;
        border: 1px solid rgba(82, 82, 82, 0.2) !important;
        border-radius: var(--radius) !important;
        background: rgba(24, 24, 27, 0.45) !important;
        backdrop-filter: blur(12px) !important;
        padding: 1rem !important;
    }}

    .chat-history-strict {{
        flex-grow: 1 !important;
        overflow-y: auto !important;
        padding-right: 0.5rem !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 1rem !important;
    }}

    .chat-history-strict::-webkit-scrollbar {{
        width: 6px;
    }}
    .chat-history-strict::-webkit-scrollbar-thumb {{
        background: rgba(255, 255, 255, 0.1);
        border-radius: 3px;
    }}

    .chat-input-strict {{
        flex-none !important;
        padding-top: 1rem !important;
        border-top: 1px solid rgba(82, 82, 82, 0.2) !important;
        margin-top: 1rem !important;
    }}

    h1 {{ 
        font-size: 3.5rem !important; 
        font-weight: 800 !important;
        letter-spacing: -0.05em !important;
        background: linear-gradient(to bottom right, #fff 40%, rgba(255,255,255,0.4));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem !important;
        text-align: center;
    }}

    .stMetric {{
        background: rgba(24, 24, 27, 0.6) !important;
        padding: 1rem !important;
        border-radius: var(--radius) !important;
        border: 1px solid rgba(39, 39, 42, 1) !important;
    }}

    /* Shadcn/UI Inputs & Buttons */
    .stButton>button {{
        background-color: rgb(250, 250, 250) !important;
        color: rgb(9, 9, 11) !important;
        border-radius: 0.5rem !important;
        font-weight: 500 !important;
    }}
    
    input, textarea, select {{
        background-color: rgb(9, 9, 11) !important;
        color: white !important;
        border: 1px solid rgba(39, 39, 42, 1) !important;
        border-radius: 0.375rem !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- Initialization & State ---
if 'df' not in st.session_state: st.session_state.df = backend.load_vault()
if 'research_results' not in st.session_state: st.session_state.research_results = None
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'extracted_context' not in st.session_state: st.session_state.extracted_context = ""
if 'usecase' not in st.session_state: st.session_state.usecase = "BUSINESS_SALES"
if 'google_creds' not in st.session_state: st.session_state.google_creds = None
if 'user_skillset' not in st.session_state: st.session_state.user_skillset = ""

DEFAULT_PROMPT_TEMPLATE = """Role: Senior Sales Development Representative (SDR)
Target Person: {name}
Target Company: {company}
Target Profession: {profession}
Mode/Mission: {mode}

Sender's Value Proposition & Context:
{context}

TASK: Write a highly personalized, low-friction cold email. 

STRICT GUIDELINES:
1. Keep it under 100 words.
2. Hook them with a relevant observation related to their company/role.
3. Focus on ONE specific problem we solve for them.
4. End with a soft call-to-action.

OUTPUT: Return ONLY the email body."""

if 'email_prompt_template' not in st.session_state:
    st.session_state.email_prompt_template = DEFAULT_PROMPT_TEMPLATE

def get_unified_context():
    context = "### LEARNED INTELLIGENCE & MISSION PARAMETERS\n\n"
    context += f"CURRENT PROTOCOL: {st.session_state.usecase}\n"
    if st.session_state.user_skillset:
        context += f"USER SKILLSET/IDENTITY: {st.session_state.user_skillset}\n"
    context += "\n"
    if st.session_state.extracted_context:
        context += "PRIMARY INTEL:\n" + st.session_state.extracted_context + "\n\n"
    if st.session_state.df is not None and not st.session_state.df.empty:
        context += f"VAULT SUMMARY: {len(st.session_state.df)} leads indexed.\n"
    return context

# --- Sidebar ---
with st.sidebar:
    st.markdown("### Executive Panel")
    gemini_key = st.text_input("Access Security Key", type="password")
    
    st.divider()
    st.subheader("Mission Focus")
    st.session_state.usecase = st.selectbox("Objective", ["BUSINESS_SALES", "JOB_HUNTING"])
    st.session_state.user_skillset = st.text_area("User Identity Profile", value=st.session_state.user_skillset)
    
    st.divider()
    st.subheader("Intelligence Input")
    uploaded_files = st.file_uploader("Personnel Files", type=["pdf", "docx", "txt"], accept_multiple_files=True)
    if uploaded_files:
        if st.button("SYNC SYSTEM KNOWLEDGE", use_container_width=True):
            combined_text = ""
            for f in uploaded_files: combined_text += f"\n--- {f.name} ---\n" + backend.extract_text_from_file(f)
            st.session_state.extracted_context = combined_text
            st.success("Synced.")
    
    st.divider()
    st.subheader("Communication Protocol")
    client_id = st.text_input("Google Client ID", type="password")
    client_secret = st.text_input("Google Client Secret", type="password")
    if client_id and client_secret:
        st.session_state.google_client_config = {"web": {"client_id": client_id, "client_secret": client_secret, "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token"}}
        if st.session_state.google_creds is None:
            auth_url = backend.get_google_auth_url(st.session_state.google_client_config, "http://localhost:8501/")
            st.link_button("Authorize Gmail", auth_url, use_container_width=True)
        else: st.success("Gmail API Active")

# --- Main Layout ---
st.markdown("<h1>OUTREACH BRAIN</h1>", unsafe_allow_html=True)
m1, m2, m3 = st.columns(3)
m1.metric("VAULT NODES", len(st.session_state.df) if st.session_state.df is not None else 0)
m2.metric("INTEL NODES", f"{len(st.session_state.extracted_context)} chars")
m3.metric("PROTOCOL", st.session_state.usecase)

tab_finder, tab_strategy, tab_vault, tab_neural, tab_launch, tab_analytics = st.tabs([
    "Lead Prospecting", "AI Strategy", "Intelligence Vault", "Neural Drafting", "Mission Launch", "Analytics"
])

with tab_finder:
    st.subheader("Global Prospecting")
    search_query = st.text_input("Mission Sector", placeholder="e.g., Venture Capitalists in Gurgaon")
    if st.button("Execute Global Research", use_container_width=True):
        if gemini_key and search_query:
            with st.spinner("Automating Research Protocol..."):
                final_prompt = backend.generate_search_prompt(search_query)
                res = backend.search_and_extract_leads(search_query, gemini_key, st.session_state.usecase, final_prompt)
                st.session_state.research_results = res

    if st.session_state.research_results is not None:
        st.dataframe(st.session_state.research_results, use_container_width=True)
        if st.button("Secure to Vault"):
            if st.session_state.df is None: st.session_state.df = st.session_state.research_results
            else: st.session_state.df = pd.concat([st.session_state.df, st.session_state.research_results]).drop_duplicates(subset=['id', 'contact_email', 'name'])
            backend.save_vault(st.session_state.df)
            st.success("Nodes secured.")

with tab_strategy:
    st.subheader("AI Strategic Brain")
    
    # 6.7 Start Flexbox Chat Viewport
    st.markdown('<div class="chat-viewport-strict">', unsafe_allow_html=True)
    
    # 1. Message History Area (The Middle)
    st.markdown('<div class="chat-history-strict">', unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        with st.chat_message("user" if msg["role"] == "user" else "assistant"):
            st.markdown(msg["content"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 2. Input Area (The Bottom)
    st.markdown('<div class="chat-input-strict">', unsafe_allow_html=True)
    if prompt := st.chat_input("Enter strategic query..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        # Call strategist
        if gemini_key:
            client = genai.Client(api_key=gemini_key)
            gemini_history = [{"role": ("user" if m["role"] == "user" else "model"), "parts": [{"text": m["content"]}]} for m in st.session_state.chat_history]
            response = backend.get_strategist_response(client, gemini_history, get_unified_context())
            st.session_state.chat_history.append({"role": "model", "content": response})
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    # 6.7 End Flexbox Chat Viewport

with tab_vault:
    head_col, action_col = st.columns([4, 1])
    head_col.subheader("Intelligence Vault")
    
    if st.session_state.df is not None:
        enrich_btn = action_col.button("⚡ Enrich Data", use_container_width=True, type="primary")
        
        vault_placeholder = st.empty()
        vault_placeholder.dataframe(st.session_state.df, use_container_width=True)
        
        if enrich_btn:
            with st.spinner("Executing Smart Enrichment Protocol..."):
                for index, row in st.session_state.df.iterrows():
                    current_email = str(row.get("contact_email", "")).strip()
                    # Only enrich if missing, invalid, or generic
                    if not current_email or backend.is_generic_email(current_email) or not backend.is_valid_email(current_email):
                        # Visual Feedback: Scanning...
                        st.session_state.df.at[index, "contact_email"] = "Scanning..."
                        vault_placeholder.dataframe(st.session_state.df, use_container_width=True)
                        
                        # Actual Logic
                        new_email = backend.smart_enrich_single_lead(row.to_dict())
                        st.session_state.df.at[index, "contact_email"] = new_email
                        
                        # Update UI
                        vault_placeholder.dataframe(st.session_state.df, use_container_width=True)
                        time.sleep(0.1) # Smoothness
                
                backend.save_vault(st.session_state.df)
                st.success("Vault Intelligence Enriched.")
                st.rerun()

        if st.button("Wipe Vault"):
            st.session_state.df = None
            if os.path.exists("vault.csv"): os.remove("vault.csv")
            st.rerun()

with tab_neural:
    st.subheader("Neural Drafting")
    if st.button("Execute Batch Synthesis", use_container_width=True):
        if gemini_key and st.session_state.df is not None:
            st.session_state.df = backend.generate_email_drafts(st.session_state.df, gemini_key, get_unified_context(), st.session_state.email_prompt_template)
            backend.save_vault(st.session_state.df)
            st.success("Batch complete.")
    if st.session_state.df is not None: st.data_editor(st.session_state.df, use_container_width=True)

with tab_launch:
    st.subheader("Mission Launch")
    if st.button("Initiate Dispatch", use_container_width=True):
        if st.session_state.google_creds:
            results = backend.send_batch_emails_api(st.session_state.df, st.session_state.google_creds)
            backend.save_vault(st.session_state.df)
            st.success(f"Sent {results['sent']} communications.")

with tab_analytics:
    st.subheader("Analytics")
    if st.session_state.df is not None:
        st.bar_chart(st.session_state.df["send_status"].value_counts())

st.divider()
st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.4); font-size: 0.7rem;'>VERSION 6.7 | VIEWPORT LOCK 2.0</p>", unsafe_allow_html=True)
