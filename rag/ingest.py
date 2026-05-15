"""
Astra Enterprise — RAG Ingestion Pipeline
Reads all documents from data/ folder, chunks them,
generates Gemini embeddings, stores in Supabase pgvector
"""

import os
import json
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from supabase import create_client
import pypdf
import csv

load_dotenv()

# ── Clients ──────────────────────────────────────
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

EMBED_MODEL = "gemini-embedding-001"
CHUNK_SIZE  = 800
CHUNK_OVERLAP = 100

# ── Department mapping ────────────────────────────
DEPT_MAP = {
    "hr_docs":      "hr",
    "sales_docs":   "sales",
    "finance_docs": "finance",
}

# ── Chunking ──────────────────────────────────────
def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+size])
        chunks.append(chunk)
        i += size - overlap
    return [c for c in chunks if len(c.strip()) > 50]

# ── File readers ──────────────────────────────────
def read_pdf(path: Path) -> str:
    reader = pypdf.PdfReader(str(path))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()

def read_csv(path: Path) -> str:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(", ".join(f"{k}: {v}" for k, v in row.items()))
    return "\n".join(rows)

def read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return read_pdf(path)
    elif path.suffix.lower() == ".csv":
        return read_csv(path)
    elif path.suffix.lower() in [".txt", ".md"]:
        return path.read_text(encoding="utf-8")
    return ""

# ── Embedding ─────────────────────────────────────
def get_embedding(text: str) -> list:
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=text,
        config={"output_dimensionality": 1536}
    )
    return result.embeddings[0].values

# ── Main ingestion ────────────────────────────────
def ingest_all():
    data_dir = Path(__file__).parent.parent / "data"
    total_chunks = 0

    print("\n🚀 Starting Astra RAG Ingestion Pipeline")
    print("=" * 50)

    # Clear existing documents
    supabase.table("documents").delete().neq("id", 0).execute()
    print("🗑️  Cleared existing documents\n")

    for folder, department in DEPT_MAP.items():
        folder_path = data_dir / folder
        if not folder_path.exists():
            print(f"⚠️  Folder not found: {folder_path}")
            continue

        files = list(folder_path.iterdir())
        print(f"📁 Processing {folder} ({len(files)} files) → dept: {department}")

        for file_path in files:
            if file_path.suffix.lower() not in [".pdf", ".csv", ".txt", ".md"]:
                continue

            print(f"   📄 {file_path.name}", end=" ")

            try:
                raw_text = read_file(file_path)
                if not raw_text:
                    print("⚠️  Empty — skipped")
                    continue

                chunks = chunk_text(raw_text)
                print(f"→ {len(chunks)} chunks", end=" ")

                for i, chunk in enumerate(chunks):
                    time.sleep(3)
                    embedding = get_embedding(chunk)

                    supabase.table("documents").insert({
                        "content":     chunk,
                        "embedding":   embedding,
                        "source_file": file_path.name,
                        "doc_type":    file_path.suffix.lower().replace(".", ""),
                        "department":  department,
                        "metadata": {
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "file_path": str(file_path),
                        }
                    }).execute()

                total_chunks += len(chunks)
                print(f"✅")

            except Exception as e:
                print(f"❌ Error: {e}")

    print("\n" + "=" * 50)
    print(f"✅ Ingestion complete! Total chunks stored: {total_chunks}")
    print(f"📊 Check your Supabase dashboard to verify")

if __name__ == "__main__":
    ingest_all()