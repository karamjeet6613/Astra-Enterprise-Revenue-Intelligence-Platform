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

elif page == "📊 Sales Copilot":
    st.markdown("## 📊 Sales Copilot")
    st.caption("Revenue analytics and pipeline intelligence — powered by Astra AI")
    st.divider()

    import pandas as pd
    import plotly.express as px

    DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "sales_docs")

    @st.cache_data
    def load_data():
        revenue_df = pd.read_csv(os.path.join(DATA_DIR, "revenue_by_region_2024.csv"))
        pipeline_df = pd.read_csv(os.path.join(DATA_DIR, "pipeline_deals_Q1_2025.csv"))
        reps_df = pd.read_csv(os.path.join(DATA_DIR, "sales_rep_performance_2024.csv"))
        return revenue_df, pipeline_df, reps_df

    revenue_df, pipeline_df, reps_df = load_data()

    # ── KPI Row ──────────────────────────────────
    total_rev = revenue_df["Revenue_USD"].sum()
    total_target = revenue_df["Target_USD"].sum()
    attainment = round(total_rev / total_target * 100, 1)
    total_pipeline = pipeline_df["ARR_USD"].sum()
    avg_deal = pipeline_df["ARR_USD"].mean()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Revenue FY2024", f"${total_rev/1e6:.1f}M", f"{attainment}% of target")
    k2.metric("Total Target", f"${total_target/1e6:.1f}M")
    k3.metric("Q1 2025 Pipeline", f"${total_pipeline/1e6:.1f}M")
    k4.metric("Avg Deal Size", f"${avg_deal/1e3:.0f}K")

    st.divider()

    # ── Charts Row ───────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Revenue vs Target by Region**")
        region_data = revenue_df.groupby("Region").agg(
            Revenue=("Revenue_USD", "sum"),
            Target=("Target_USD", "sum")
        ).reset_index()
        fig1 = px.bar(region_data, x="Region",
                      y=["Revenue", "Target"],
                      barmode="group",
                      color_discrete_map={"Revenue": "#0f3460", "Target": "#e94560"},
                      height=320)
        fig1.update_layout(margin=dict(t=20, b=20), legend_title="")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("**Quarterly Revenue Trend**")
        q_data = revenue_df.groupby("Quarter")["Revenue_USD"].sum().reset_index()
        fig2 = px.line(q_data, x="Quarter", y="Revenue_USD",
                       markers=True, height=320,
                       color_discrete_sequence=["#0f3460"])
        fig2.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("**Pipeline by Stage (Q1 2025)**")
        stage_data = pipeline_df.groupby("Stage")["ARR_USD"].sum().reset_index()
        fig3 = px.pie(stage_data, values="ARR_USD", names="Stage",
                      height=320,
                      color_discrete_sequence=px.colors.sequential.Blues_r)
        fig3.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("**Sales Rep Leaderboard**")
        top_reps = reps_df.nlargest(8, "Quota_Attainment_Pct")[
            ["Rep_Name", "Region", "Quota_Attainment_Pct", "Annual_Attain_USD"]
        ].copy()
        top_reps["Annual_Attain_USD"] = top_reps["Annual_Attain_USD"].apply(
            lambda x: f"${x/1e6:.2f}M"
        )
        top_reps.columns = ["Rep", "Region", "Attainment %", "Revenue"]
        st.dataframe(top_reps, use_container_width=True, hide_index=True, height=320)

    st.divider()

    # ── AI Q&A ───────────────────────────────────
    st.markdown("**💬 Ask Astra Sales Copilot**")
    st.caption("Ask revenue questions and get AI-powered insights")

    sample_qs = [
        "Why did APAC revenue drop?",
        "Who are the top performers?",
        "What is our pipeline health?",
        "Which region is overperforming?",
        "What deals are at risk?",
        "Suggest actions to improve LATAM",
    ]
    cols = st.columns(3)
    for i, q in enumerate(sample_qs):
        with cols[i % 3]:
            if st.button(q, key=f"sales_q_{i}", use_container_width=True):
                st.session_state.sales_question = q

    if "sales_messages" not in st.session_state:
        st.session_state.sales_messages = []
    if "sales_question" not in st.session_state:
        st.session_state.sales_question = ""

    for msg in st.session_state.sales_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    question = st.chat_input("Ask a sales question...") or st.session_state.sales_question
    if st.session_state.sales_question:
        st.session_state.sales_question = ""

    if question:
        st.session_state.sales_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing sales data..."):
                try:
                    from agents.sales_copilot import ask_sales
                    result = ask_sales(question)
                    st.write(result["answer"])
                    st.session_state.sales_messages.append({
                        "role": "assistant",
                        "content": result["answer"]
                    })
                except Exception as e:
                    st.error(f"Error: {e}")

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