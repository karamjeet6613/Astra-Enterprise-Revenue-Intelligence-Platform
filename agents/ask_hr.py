"""
Astra Enterprise — AskHR Agent
Answers employee HR questions using RAG over HR policy documents
"""

import os
from dotenv import load_dotenv
from groq import Groq
from rag.retriever import retrieve, format_context

load_dotenv()

import httpx
groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    http_client=httpx.Client()
)

SYSTEM_PROMPT = """You are AskHR, an intelligent HR assistant for NexaCore Technologies.
You answer employee questions accurately based ONLY on the company HR policies provided.
Always cite which document your answer comes from.
If the answer is not in the provided context, say so clearly — do not guess.
Be professional, empathetic, and concise.
Format your response clearly with bullet points where appropriate."""

def ask_hr(question: str, chat_history: list = []) -> dict:
    # Retrieve relevant HR docs
    docs = retrieve(question, department="hr", top_k=5, threshold=0.2)
    context = format_context(docs)

    # Build messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""
HR Policy Context:
{context}

Employee Question: {question}

Please answer based on the policy context above. Cite your sources.
"""}
    ]

    # Get answer from Groq
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.2,
        max_tokens=1000
    )

    answer = response.choices[0].message.content

    # Extract sources
    sources = list(set([doc["source_file"] for doc in docs]))

    return {
        "answer": answer,
        "sources": sources,
        "docs_found": len(docs),
        "context": context
    }