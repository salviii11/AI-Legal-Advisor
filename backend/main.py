import os
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# On Vercel or serverless environments where root is read-only, use /tmp for sqlite
if os.getenv("VERCEL") or not os.access(BASE_DIR, os.W_OK):
    DB_PATH = Path(tempfile.gettempdir()) / "legal_advisor.db"
else:
    DB_PATH = BASE_DIR / "legal_advisor.db"

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".txt", ".pdf"}

app = FastAPI(
    title="AI Legal Advisor API",
    description="Educational legal-information prototype. Not a substitute for a lawyer.",
    version="1.0.0",
)

allowed_origins_env = os.getenv("CORS_ORIGINS", "*")
origins = ["*"] if allowed_origins_env == "*" else [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    jurisdiction: str = Field(default="India", max_length=100)


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    mode: str
    history_id: int


def db_connect():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with db_connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                jurisdiction TEXT NOT NULL,
                mode TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


init_db()


def build_ai_client():
    api_key = os.getenv("LLM_API_KEY", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "").strip() or None
    if not api_key or OpenAI is None:
        return None
    try:
        return OpenAI(api_key=api_key, base_url=base_url)
    except Exception:
        return None


def demo_answer(question: str, jurisdiction: str) -> str:
    return (
        "This is a demo response because an AI provider has not been configured.\\n\\n"
        f"Your question: {question}\\n"
        f"Jurisdiction selected: {jurisdiction}\\n\\n"
        "Next steps: identify the relevant legal topic, check current official legislation or "
        "government guidance for your jurisdiction, and keep a record of relevant dates and documents. "
        "This prototype has not verified the legal merits of your situation. Please consult a qualified "
        "legal professional for advice about a specific case."
    )


def generate_answer(question: str, jurisdiction: str):
    client = build_ai_client()
    model = os.getenv("LLM_MODEL", "").strip()
    if not client or not model:
        return demo_answer(question, jurisdiction), "demo", []

    system_prompt = (
        "You are an educational legal-information assistant, not a lawyer. "
        "Explain general legal concepts in plain language. The stated jurisdiction is "
        f"{jurisdiction}. Do not invent statutes, case names, citations, or URLs. "
        "If you cannot verify a specific legal claim from provided evidence, say so. "
        "Ask for clarification when jurisdiction or facts are essential. Do not promise outcomes. "
        "End with a concise reminder to consult a qualified lawyer for case-specific advice. "
        "No curated legal source retrieval is connected in this starter project yet."
    )
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.2,
        )
        answer = response.choices[0].message.content or "The AI provider returned an empty response."
        return answer, "llm", []
    except Exception:
        # Do not return provider errors or secrets to the browser.
        return (
            "The AI service could not be reached. Check your backend configuration and provider status. "
            "No legal answer was generated. Please try again later or consult a qualified legal professional."
        ), "error", []


@app.get("/", response_class=HTMLResponse)
def root():
    candidates = [
        BASE_DIR.parent / "frontend" / "index.html",
        BASE_DIR.parent / "index.html",
        BASE_DIR / "index.html",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return HTMLResponse(content=candidate.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>AI Legal Advisor API</h1><p>Running successfully. Check <a href='/docs'>/docs</a>.</p>")


@app.get("/api/health")
@app.get("/health")
def health():
    return {
        "status": "ok",
        "ai_configured": bool(os.getenv("LLM_API_KEY", "").strip() and os.getenv("LLM_MODEL", "").strip()),
        "disclaimer": "General legal information only; not a substitute for a qualified lawyer."
    }


@app.post("/api/chat", response_model=ChatResponse)
@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    question = payload.question.strip()
    if len(question) < 2:
        raise HTTPException(status_code=422, detail="Please enter a longer question.")
    answer, mode, sources = generate_answer(question, payload.jurisdiction.strip() or "India")
    created_at = datetime.now(timezone.utc).isoformat()
    with db_connect() as conn:
        cursor = conn.execute(
            "INSERT INTO history (question, answer, jurisdiction, mode, created_at) VALUES (?, ?, ?, ?, ?)",
            (question, answer, payload.jurisdiction.strip() or "India", mode, created_at),
        )
        history_id = cursor.lastrowid
        conn.commit()
    return ChatResponse(answer=answer, sources=sources, mode=mode, history_id=history_id)


@app.get("/api/history")
@app.get("/history")
def get_history(limit: int = 20):
    limit = max(1, min(limit, 100))
    with db_connect() as conn:
        rows = conn.execute(
            "SELECT id, question, answer, jurisdiction, mode, created_at FROM history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return {"items": [dict(row) for row in rows]}


@app.delete("/api/history")
@app.delete("/history")
def clear_history():
    with db_connect() as conn:
        conn.execute("DELETE FROM history")
        conn.commit()
    return {"message": "Local query history cleared."}


@app.post("/api/documents/extract")
@app.post("/documents/extract")
async def extract_document(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported in this starter version.")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large. Maximum size is 5 MB.")
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    try:
        if suffix == ".txt":
            extracted = content.decode("utf-8", errors="replace")
        else:
            if PdfReader is None:
                raise HTTPException(status_code=500, detail="PDF support is unavailable. Install requirements.txt.")
            import io
            reader = PdfReader(io.BytesIO(content))
            extracted = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="The file could not be read. Try another PDF or TXT file.")

    extracted = extracted.strip()
    if not extracted:
        raise HTTPException(status_code=400, detail="No readable text was found. Scanned PDFs may require OCR, which is not included.")
    return {
        "filename": Path(file.filename or "document").name,
        "characters": len(extracted),
        "text": extracted[:30000],
        "notice": "Text extraction only. This endpoint does not yet provide legal document review or legal advice."
    }
