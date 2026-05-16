import streamlit as st
import base64
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Load from Streamlit secrets if available (production)
for key in ["GEMINI_API_KEY", "GROQ_API_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_KEY"]:
    if key in st.secrets:
        os.environ[key] = st.secrets[key]

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
    page = st.radio("Navigation", [
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
        st.info("**🤖 AI Copilot**\n\nGeneral enterprise AI assistant powered by Groq LLaMA 3.3")
    with col2:
        st.success("**❓ AskHR**\n\nInstant HR policy answers from your company documents")
    with col3:
        st.warning("**📊 Sales Copilot**\n\nRevenue analytics and pipeline intelligence")

elif page == "🤖 AI Copilot":
    st.markdown("## 🤖 AI Copilot")
    st.caption("General purpose enterprise assistant — powered by Groq LLaMA 3.3")
    st.divider()

    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = []

    for msg in st.session_state.copilot_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask anything..."):
        st.session_state.copilot_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    from groq import Groq
                    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                    response = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": "You are Astra, an intelligent enterprise AI assistant for NexaCore Technologies. Be helpful, concise, and professional."},
                            *[{"role": m["role"], "content": m["content"]} for m in st.session_state.copilot_messages]
                        ],
                        temperature=0.7,
                        max_tokens=1000
                    )
                    answer = response.choices[0].message.content
                    st.write(answer)
                    st.session_state.copilot_messages.append({
                        "role": "assistant",
                        "content": answer
                    })
                except Exception as e:
                    st.error(f"Error: {e}")

elif page == "❓ AskHR":
    st.markdown("## ❓ AskHR")
    st.caption("Ask any HR question — answers pulled directly from NexaCore HR policy documents")
    st.divider()

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
            if st.button(q, key=f"sq_{i}", width='stretch'):
                st.session_state.hr_question = q

    st.divider()

    if "hr_messages" not in st.session_state:
        st.session_state.hr_messages = []
    if "hr_question" not in st.session_state:
        st.session_state.hr_question = ""

    for msg in st.session_state.hr_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sources"):
                with st.expander("📄 Sources"):
                    for src in msg["sources"]:
                        st.caption(f"• {src}")

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
    st.caption("Revenue analytics and pipeline intelligence — powered by Astra AI")

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
    won = pipeline_df[pipeline_df["Stage"] == "Closed Won"]["ARR_USD"].sum()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("FY2024 Revenue", f"${total_rev/1e6:.1f}M", f"{attainment}% of target")
    k2.metric("Target", f"${total_target/1e6:.1f}M")
    k3.metric("Q1 2025 Pipeline", f"${total_pipeline/1e6:.1f}M")
    k4.metric("Avg Deal Size", f"${avg_deal/1e3:.0f}K")
    k5.metric("Closed Won", f"${won/1e3:.0f}K")

    # ── 3 Charts in one row ───────────────────────
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("**Revenue vs Target by Region**")
        region_data = revenue_df.groupby("Region").agg(
            Revenue=("Revenue_USD", "sum"),
            Target=("Target_USD", "sum")
        ).reset_index()
        fig1 = px.bar(region_data, x="Region",
                      y=["Revenue", "Target"],
                      barmode="group",
                      color_discrete_map={"Revenue": "#0f3460", "Target": "#e94560"},
                      height=200)
        fig1.update_layout(margin=dict(t=10, b=10, l=10, r=10),
                           legend_title="", legend=dict(orientation="h", y=-0.3),
                           font=dict(size=10))
        st.plotly_chart(fig1, width='stretch')

    with c2:
        st.markdown("**Quarterly Revenue Trend**")
        q_data = revenue_df.groupby("Quarter")["Revenue_USD"].sum().reset_index()
        fig2 = px.line(q_data, x="Quarter", y="Revenue_USD",
                       markers=True, height=200,
                       color_discrete_sequence=["#0f3460"])
        fig2.update_layout(margin=dict(t=10, b=10, l=10, r=10),
                           font=dict(size=10))
        st.plotly_chart(fig2, width='stretch')

    with c3:
        st.markdown("**Pipeline by Stage**")
        stage_data = pipeline_df.groupby("Stage")["ARR_USD"].sum().reset_index()
        fig3 = px.pie(stage_data, values="ARR_USD", names="Stage",
                      height=200,
                      color_discrete_sequence=px.colors.sequential.Blues_r)
        fig3.update_layout(margin=dict(t=10, b=10, l=10, r=10),
                           font=dict(size=9),
                           showlegend=False)
        st.plotly_chart(fig3, width='stretch')

    # ── Leaderboard + Region Attainment ──────────
    l1, l2 = st.columns(2)

    with l1:
        st.markdown("**🏆 Rep Leaderboard**")
        top_reps = reps_df.nlargest(5, "Quota_Attainment_Pct")[
            ["Rep_Name", "Region", "Quota_Attainment_Pct", "Annual_Attain_USD"]
        ].copy()
        top_reps["Annual_Attain_USD"] = top_reps["Annual_Attain_USD"].apply(
            lambda x: f"${x/1e6:.2f}M"
        )
        top_reps.columns = ["Rep", "Region", "Attain %", "Revenue"]
        st.dataframe(top_reps, width='stretch', hide_index=True, height=185)

    with l2:
        st.markdown("**🌍 Attainment by Region**")
        region_att = revenue_df.groupby("Region").agg(
            Revenue=("Revenue_USD", "sum"),
            Target=("Target_USD", "sum")
        ).reset_index()
        region_att["Attainment"] = (region_att["Revenue"] / region_att["Target"] * 100).round(1)
        fig4 = px.bar(region_att, x="Attainment", y="Region",
                      orientation="h", height=185,
                      color="Attainment",
                      color_continuous_scale=["#e94560", "#f5a623", "#0f3460"],
                      text="Attainment")
        fig4.update_traces(texttemplate="%{text}%", textposition="outside")
        fig4.update_layout(margin=dict(t=10, b=10, l=10, r=30),
                           font=dict(size=10),
                           coloraxis_showscale=False)
        st.plotly_chart(fig4, width='stretch')

    # ── AI Chat in expander ───────────────────────
    with st.expander("💬 Ask Astra Sales Copilot", expanded=False):
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
                if st.button(q, key=f"sales_q_{i}", width='stretch'):
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