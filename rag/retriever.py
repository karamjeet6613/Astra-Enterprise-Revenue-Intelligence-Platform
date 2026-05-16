"""
Astra Enterprise — RAG Retriever
Converts user query → embedding → similarity search → returns relevant chunks
"""

import os
from dotenv import load_dotenv
try:
    from google import genai
except ImportError:
    import google.generativeai as genai
from supabase import create_client

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

EMBED_MODEL = "gemini-embedding-001"

def get_query_embedding(query: str) -> list:
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=query,
        config={"output_dimensionality": 1536}
    )
    return result.embeddings[0].values

def retrieve(query: str, department: str = None, top_k: int = 5, threshold: float = 0.3) -> list:
    embedding = get_query_embedding(query)
    result = supabase.rpc("match_documents", {
        "query_embedding": embedding,
        "match_threshold": threshold,
        "match_count": top_k,
        "filter_department": department
    }).execute()
    return result.data or []

def format_context(docs: list) -> str:
    if not docs:
        return "No relevant documents found."
    context = ""
    for i, doc in enumerate(docs, 1):
        context += f"\n[Source {i}: {doc['source_file']} | Dept: {doc['department']}]\n"
        context += doc['content'] + "\n"
    return context.strip()