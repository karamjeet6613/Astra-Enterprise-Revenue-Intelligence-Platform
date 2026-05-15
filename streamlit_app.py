import streamlit as st
import base64
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# ── Page config ────────────────────────────────
st.set_page_config(
    page_title="Astra — Enterprise Revenue Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Load SVG logo ──────────────────────────────
def get_svg_logo(size: int = 36) -> str:
    svg_path = os.path.join(os.path.dirname(__file__), "assets", "astra-ai-icon.svg")
    with open(svg_path, "r") as f:
        svg = f.read()
    b64 = base64.b64encode(svg.encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}" width="{size}" height="{size}" style="vertical-align:middle; margin-right:8px;">'

# ── Sidebar ────────────────────────────────────
with st.sidebar:
    st.markdown(f'{get_svg_logo(40)} <span style="font-size:1.3rem;font-weight:700;">Astra</span>', unsafe_allow_html=True)
    st.caption("Enterprise Revenue Intelligence Platform")
    st.divider()
    st.markdown("**Navigation**")
    page = st.radio("", [
        "🏠 Home",
        "🤖 AI Copilot",
        "❓ AskHR",
        "📊 Sales Copilot",
    ], label_visibility="collapsed")
    st.divider()
    st.caption("NexaCore Technologies Inc.")
    st.caption("Demo 2 — RAG + Enterprise Data")

# ── Pages ──────────────────────────────────────

if page == "🏠 Home":
    st.markdown(f'## {get_svg_logo(32)} Welcome to Astra', unsafe_allow_html=True)
    st.markdown("#### Enterprise AI Workflow Intelligence Platform")
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**🤖 AI Copilot**\n\nGeneral enterprise AI assistant powered by Gemini + Groq")
    with col2:
        st.success("**❓ AskHR**\n\nInstant HR policy answers from your company documents")
    with col3:
        st.warning("**📊 Sales Copilot**\n\nRevenue analytics and pipeline intelligence")

elif page == "🤖 AI Copilot":
    st.markdown("## 🤖 AI Copilot")
    st.caption("General purpose enterprise assistant")
    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = []
    for msg in st.session_state.copilot_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    if prompt := st.chat_input("Ask anything..."):
        st.session_state.copilot_messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            st.write("AI Copilot coming in Demo 2 build — stay tuned!")

elif page == "❓ AskHR":
    st.markdown("## ❓ AskHR")
    st.caption("Ask any HR question — answers pulled directly from NexaCore HR policy documents")
    st.divider()

    # Sample questions
    st.markdown("**💡 Try asking:**")
    cols = st.columns(3)
    sample_questions = [
        "How many PTO days do I get?",
        "What is the maternity leave policy?",
        "How does the bonus structure work?",
        "What is the notice period?",
        "How do I apply for sick leave?",
        "What is the 401k matching policy?",
    ]
    for i, q in enumerate(sample_questions):
        with cols[i % 3]:
            if st.button(q, key=f"sq_{i}", use_container_width=True):
                st.session_state.hr_question = q

    st.divider()

    # Chat interface
    if "hr_messages" not in st.session_state:
        st.session_state.hr_messages = []
    if "hr_question" not in st.session_state:
        st.session_state.hr_question = ""

    # Display chat history
    for msg in st.session_state.hr_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sources"):
                with st.expander("📄 Sources"):
                    for src in msg["sources"]:
                        st.caption(f"• {src}")

    # Input
    question = st.chat_input("Ask an HR question...") or st.session_state.hr_question
    if st.session_state.hr_question:
        st.session_state.hr_question = ""

    if question:
        st.session_state.hr_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching HR policies..."):
                try:
                    from agents.ask_hr import ask_hr
                    result = ask_hr(question)
                    st.write(result["answer"])
                    if result["sources"]:
                        with st.expander(f"📄 Sources ({result['docs_found']} documents found)"):
                            for src in result["sources"]:
                                st.caption(f"• {src}")
                    st.session_state.hr_messages.append({
                        "role": "assistant",
                        "content": result["answer"],
                        "sources": result["sources"]
                    })
                except Exception as e:
                    st.error(f"Error: {e}")

elif page == "📊 Sales Copilot":
    st.markdown("## 📊 Sales Copilot")
    st.caption("Revenue analytics and pipeline intelligence — coming next!")
    st.info("🚧 Building in Step 5...")