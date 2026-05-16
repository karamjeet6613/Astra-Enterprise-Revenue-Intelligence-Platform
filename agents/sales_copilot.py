import os
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
from rag.retriever import retrieve, format_context

load_dotenv()

import httpx
groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    http_client=httpx.Client()
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sales_docs")

SYSTEM_PROMPT = (
    "You are Astra Sales Copilot, an elite revenue intelligence assistant for NexaCore Technologies. "
    "You analyze sales data, identify trends, explain performance gaps, and suggest actions. "
    "Always be specific with numbers, percentages, and comparisons from the data provided. "
    "Structure your response with: Key Finding, Root Cause, Recommended Action. "
    "Be direct and executive-ready."
)

def load_sales_data():
    revenue_df = pd.read_csv(os.path.join(DATA_DIR, "revenue_by_region_2024.csv"))
    pipeline_df = pd.read_csv(os.path.join(DATA_DIR, "pipeline_deals_Q1_2025.csv"))
    reps_df = pd.read_csv(os.path.join(DATA_DIR, "sales_rep_performance_2024.csv"))
    return revenue_df, pipeline_df, reps_df

def get_data_summary():
    revenue_df, pipeline_df, reps_df = load_sales_data()

    total_revenue = revenue_df["Revenue_USD"].sum()
    total_target = revenue_df["Target_USD"].sum()
    overall_attainment = round(total_revenue / total_target * 100, 1)

    region_summary = revenue_df.groupby("Region").agg(
        Revenue=("Revenue_USD", "sum"),
        Target=("Target_USD", "sum"),
    ).reset_index()
    region_summary["Attainment"] = (region_summary["Revenue"] / region_summary["Target"] * 100).round(1)

    apac = revenue_df[revenue_df["Region"] == "APAC"].groupby("Country").agg(
        Revenue=("Revenue_USD", "sum"),
        Target=("Target_USD", "sum"),
    ).reset_index()
    apac["Attainment"] = (apac["Revenue"] / apac["Target"] * 100).round(1)

    total_pipeline = pipeline_df["ARR_USD"].sum()
    by_stage = pipeline_df.groupby("Stage")["ARR_USD"].sum().reset_index()
    won = pipeline_df[pipeline_df["Stage"] == "Closed Won"]["ARR_USD"].sum()
    lost = pipeline_df[pipeline_df["Stage"] == "Closed Lost"]["ARR_USD"].sum()

    top_reps = reps_df.nlargest(3, "Quota_Attainment_Pct")[
        ["Rep_Name", "Region", "Annual_Attain_USD", "Quota_Attainment_Pct"]
    ]
    bottom_reps = reps_df.nsmallest(3, "Quota_Attainment_Pct")[
        ["Rep_Name", "Region", "Annual_Attain_USD", "Quota_Attainment_Pct"]
    ]

    lines = [
        "=== NEXACORE FY2024 SALES DATA SUMMARY ===",
        "",
        "OVERALL PERFORMANCE:",
        "- Total Revenue: ${:,.0f}".format(total_revenue),
        "- Total Target: ${:,.0f}".format(total_target),
        "- Overall Attainment: {}%".format(overall_attainment),
        "",
        "REVENUE BY REGION:",
        region_summary.to_string(index=False),
        "",
        "APAC COUNTRY BREAKDOWN:",
        apac.to_string(index=False),
        "",
        "Q1 2025 PIPELINE:",
        "- Total Pipeline Value: ${:,.0f}".format(total_pipeline),
        "- Closed Won: ${:,.0f}".format(won),
        "- Closed Lost: ${:,.0f}".format(lost),
        "- Pipeline by Stage:",
        by_stage.to_string(index=False),
        "",
        "TOP 3 REPS BY ATTAINMENT:",
        top_reps.to_string(index=False),
        "",
        "BOTTOM 3 REPS BY ATTAINMENT:",
        bottom_reps.to_string(index=False),
    ]
    return "\n".join(lines)

def ask_sales(question):
    data_summary = get_data_summary()
    docs = retrieve(question, department="sales", top_k=3, threshold=0.2)
    rag_context = format_context(docs)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            "Sales Data:\n" + data_summary +
            "\n\nAdditional Context:\n" + rag_context +
            "\n\nQuestion: " + question +
            "\n\nProvide a sharp, data-backed answer with specific numbers and actionable recommendations."
        )}
    ]

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.2,
        max_tokens=1200
    )

    return {
        "answer": response.choices[0].message.content,
        "data_summary": data_summary
    }