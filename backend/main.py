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



def generate_legal_intelligence_response(question: str, jurisdiction: str) -> str:
    q = question.lower()
    j = jurisdiction.strip() or "India"

    if any(k in q for k in ["cheque", "check", "bounced", "dishonour", "insufficient fund", "stop payment"]):
        return (
            f"⚖️ LEGAL ADVISORY: CHEQUE DISHONOUR & RECOVERY ({j.upper()})\n\n"
            f"Query: \"{question}\"\n\n"
            "1. APPLICABLE STATUTORY FRAMEWORK:\n"
            "• Sections 138 to 142 of the Negotiable Instruments Act, 1881 (NI Act).\n"
            "• Cheque dishonour for insufficient funds or exceeding account arrangement is a criminal compoundable offense.\n\n"
            "2. MANDATORY STATUTORY TIMELINES & PROCEDURE:\n"
            "• Step 1: Bank Return Memo — Obtain the formal Cheque Return Memo from the bank stating exact reason for dishonour.\n"
            "• Step 2: Statutory Demand Notice (Within 30 Days) — Within 30 days of receiving the memo, issue a legal demand notice to the drawer requiring payment within 15 days.\n"
            "• Step 3: 15-Day Cure Period — The drawer must be allowed 15 days from notice delivery to make good the payment.\n"
            "• Step 4: Filing Criminal Complaint (Within 30 Days) — If unpaid after 15 days, file a formal complaint under Section 142 NI Act before the Judicial Magistrate within 30 days.\n\n"
            "3. LIABILITIES & REMEDIES:\n"
            "• Penalties: Imprisonment for up to 2 years, or fine up to twice the cheque amount, or both.\n"
            "• Interim Compensation: Court can direct drawer to deposit up to 20% of cheque amount as interim relief under Section 143A NI Act.\n\n"
            "4. REQUIRED DOCUMENTATION:\n"
            "• Original dishonoured cheque and Bank Return Memo.\n"
            "• Copy of Legal Notice, Speed Post / Registered AD receipts, and postal delivery tracking report.\n"
            "• Invoices or agreements evidencing legally enforceable debt.\n\n"
            "Disclaimer: Educational information only. Strict limitation deadlines apply under the NI Act. Consult an advocate promptly."
        )

    elif any(k in q for k in ["cheat", "fraud", "scam", "stole", "money", "rupees", "rs", "cheated", "embezzle", "swindle", "lakh"]):
        return (
            f"⚖️ LEGAL ADVISORY: FRAUD & CRIMINAL CHEATING ({j.upper()})\n\n"
            f"Query: \"{question}\"\n\n"
            "1. APPLICABLE STATUTES & GOVERNING SECTIONS:\n"
            "• Section 318 of Bharatiya Nyaya Sanhita (BNS, 2023) [formerly Section 420 IPC - Cheating and dishonestly inducing delivery of property].\n"
            "• Section 316 BNS [formerly Section 406 IPC - Criminal Breach of Trust].\n"
            "• Section 173 of Bharatiya Nagarik Suraksha Sanhita (BNSS, 2023) [formerly Section 154 CrPC].\n\n"
            "2. STEP-BY-STEP LEGAL ACTION PLAN:\n"
            "• Step 1: Formal Police Complaint — Submit a signed complaint to the local Police Station or Economic Offences Wing (EOW) detailing the deception and monetary loss.\n"
            "• Step 2: Escalation to Superintendent of Police — If the FIR is refused, send the complaint by registered post to the SP / DCP under Section 173(4) BNSS.\n"
            "• Step 3: Application to Judicial Magistrate — If police action stalls, file an application before the Magistrate under Section 175(3) BNSS [Section 156(3) CrPC] directing police to investigate.\n"
            "• Step 4: Civil Summary Suit — File a Summary Suit under Order 37 CPC for fast-track judicial recovery of liquidated amounts.\n\n"
            "3. ESSENTIAL EVIDENCE CHECKLIST:\n"
            "• Bank account statements with highlighted transaction references (UTR/IMPS/NEFT).\n"
            "• WhatsApp messages, emails, agreements, receipts, or call recordings proving misrepresentation.\n\n"
            "Disclaimer: Educational information only. Preserve digital records and consult a criminal defense advocate."
        )

    elif any(k in q for k in ["cyber", "hacked", "phishing", "otp", "leak", "photos", "instagram", "whatsapp", "fake profile", "upi"]):
        return (
            f"⚖️ LEGAL ADVISORY: CYBER CRIME & FINANCIAL SCAMS ({j.upper()})\n\n"
            f"Query: \"{question}\"\n\n"
            "1. APPLICABLE LAWS & SECTIONS:\n"
            "• Information Technology Act, 2000 (IT Act):\n"
            "  - Section 66C: Identity theft & unauthorized electronic signature.\n"
            "  - Section 66D: Cheating by personation using computer resources.\n"
            "  - Section 66E: Privacy violation & capturing private images without consent.\n"
            "  - Section 67 / 67A: Publishing or transmitting obscene material electronically.\n"
            "• Section 318 BNS (Cheating) & Section 356 BNS (Defamation).\n\n"
            "2. IMMEDIATE GOLDEN-HOUR PROTOCOL:\n"
            "• Financial Frauds: Immediately call the National Cyber Helpline 1930 within the first 2 hours to freeze beneficiary bank accounts.\n"
            "• Online Portal: Register a formal incident at cybercrime.gov.in (National Cyber Crime Reporting Portal).\n"
            "• Bank Notification: Notify your bank's fraud prevention desk in writing within 24 hours to invoke RBI zero/limited liability rules.\n"
            "• Impersonation / Photo Leak: Report content on the hosting platform (Meta, X, Telegram) and request take-down within 24 hours under Rule 3(2)(b) of IT Rules, 2021.\n\n"
            "3. EVIDENCE PRESERVATION:\n"
            "• Full screen captures showing URLs, timestamps, sender handles, phone numbers, and transaction IDs.\n\n"
            "Disclaimer: Educational guidance. Timely reporting within the golden hour significantly improves recovery odds."
        )

    elif any(k in q for k in ["rent", "tenant", "landlord", "evict", "lease", "deposit", "flat", "pg"]):
        return (
            f"⚖️ LEGAL ADVISORY: TENANCY, EVICTION & DEPOSITS ({j.upper()})\n\n"
            f"Query: \"{question}\"\n\n"
            "1. APPLICABLE STATUTORY FRAMEWORK:\n"
            "• Model Tenancy Act, State Rent Control Acts, and Section 106 Transfer of Property Act, 1882.\n\n"
            "2. TENANT LEGAL PROTECTIONS & RIGHTS:\n"
            "• Unlawful Eviction: Landlords cannot forcefully evict a tenant or cut electricity/water supplies without a formal court decree.\n"
            "• Mandatory Notice Period: Statutory notice period (typically 30–90 days per written agreement) must precede any eviction notice.\n"
            "• Security Deposit Refund: Must be refunded upon vacating after reasonable agreed adjustments backed by demonstrable maintenance receipts.\n"
            "• Registration Mandate: Leases exceeding 11 months require compulsory registration under Section 17 Registration Act to be admissible as evidence.\n\n"
            "3. LANDLORD LEGAL RIGHTS:\n"
            "• Right to terminate on persistent rent default (exceeding 2 months), unauthorized subletting, or structural alteration without consent.\n\n"
            "4. RESOLUTION STEPS:\n"
            "• Issue a formal Legal Notice via an advocate citing tenancy clauses.\n"
            "• Approach the Rent Authority / Rent Tribunal established under the State Tenancy Act.\n\n"
            "Disclaimer: Educational information only. Review your written agreement clauses with a real estate legal counsel."
        )

    elif any(k in q for k in ["salary", "job", "employee", "employer", "termination", "fired", "wages", "pf", "relieving", "severance"]):
        return (
            f"⚖️ LEGAL ADVISORY: EMPLOYMENT, SALARY DISPUTES & TERMINATION ({j.upper()})\n\n"
            f"Query: \"{question}\"\n\n"
            "1. APPLICABLE STATUTES:\n"
            "• Payment of Wages Act, 1936 & Industrial Disputes Act, 1947.\n"
            "• State Shops & Commercial Establishments Act and Contract Labor Regulations.\n\n"
            "2. EMPLOYEE STATUTORY PROTECTIONS:\n"
            "• Withholding Salary: Employers cannot withhold earned wages for worked days. Wages must be disbursed by the 7th or 10th of each wage cycle.\n"
            "• Relieving & Experience Letter: Employer cannot arbitrarily withhold relieving documents; withholding creates actionable tortious liability for career damage.\n"
            "• Termination Without Notice: Involuntary termination requires contractually stipulated notice period or pay-in-lieu (severance) as mandated by labor statutes.\n\n"
            "3. ACTIONABLE RECOURSE PLAN:\n"
            "• Step 1: Formal Internal Demand Letter to HR and Management requesting full and final settlement within 7 days.\n"
            "• Step 2: Legal Demand Notice served through an advocate.\n"
            "• Step 3: File formal petition before the District Labor Commissioner under Section 33C(2) of Industrial Disputes Act or Labor Court.\n\n"
            "Disclaimer: Educational guidance only. Review offer letter and appointment terms with an employment lawyer."
        )

    elif any(k in q for k in ["consumer", "defective", "refund", "warranty", "product", "flipkart", "amazon", "service"]):
        return (
            f"⚖️ LEGAL ADVISORY: CONSUMER RIGHTS & REDRESSAL ({j.upper()})\n\n"
            f"Query: \"{question}\"\n\n"
            "1. APPLICABLE STATUTORY PROVISIONS:\n"
            "• Consumer Protection Act, 2019 (CPA 2019) & Consumer Protection (E-Commerce) Rules, 2020.\n\n"
            "2. CONSUMER RIGHTS & REMEDIES:\n"
            "• Right to prompt repair, replacement, or complete refund for defective goods and deficient services.\n"
            "• Relief for unfair trade practices, misleading ads, and product liability damages.\n\n"
            "3. THREE-TIER CONSUMER COMMISSIONS JURISDICTION:\n"
            "• District Commission: Claims up to ₹50 Lakhs.\n"
            "• State Commission: Claims ₹50 Lakhs to ₹2 Crores.\n"
            "• National Commission (NCDRC): Claims exceeding ₹2 Crores.\n\n"
            "4. STEP-BY-STEP FILING PROTOCOL:\n"
            "• Step 1: Formal written grievance to customer redressal with copy of purchase invoice.\n"
            "• Step 2: Dial National Consumer Helpline (1915) or register grievance via consumerhelpline.gov.in.\n"
            "• Step 3: File an online case via e-Daakhil Portal (edaakhil.nic.in). No advocate is required; consumers can appear directly.\n\n"
            "Disclaimer: Educational information only. Retain tax invoices and delivery proofs."
        )

    elif any(k in q for k in ["arrest", "bail", "police", "fir", "warrant", "custody"]):
        return (
            f"⚖️ LEGAL ADVISORY: ARREST, BAIL & POLICE POWERS ({j.upper()})\n\n"
            f"Query: \"{question}\"\n\n"
            "1. STATUTORY FRAMEWORK:\n"
            "• Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS) [formerly Code of Criminal Procedure (CrPC)].\n"
            "• Articles 21 & 22 of the Constitution of India.\n\n"
            "2. CONSTITUTIONAL & STATUTORY RIGHTS OF AN ARRESTED PERSON:\n"
            "• Right to know specific grounds of arrest immediately upon arrest.\n"
            "• Right to consult and be defended by a legal practitioner of choice.\n"
            "• Mandatory production before nearest Judicial Magistrate within 24 hours of arrest (excluding travel time).\n"
            "• D.K. Basu Guidelines: Mandatory arrest memo with date/time, signed by witness; right to have relative notified within 8-12 hours; medical examination every 48 hours.\n\n"
            "3. BAIL PROVISIONS:\n"
            "• Bailable Offences: Bail is a matter of statutory right upon furnishing surety bond (Section 478 BNSS / 436 CrPC).\n"
            "• Non-Bailable Offences: Bail is subject to judicial discretion based on nature of offense (Section 480 BNSS / 437 CrPC).\n"
            "• Anticipatory Bail: Pre-arrest protection applied before Sessions Court or High Court under Section 482 BNSS [Section 438 CrPC].\n\n"
            "Disclaimer: Educational information only. If facing imminent arrest, immediately seek urgent anticipatory bail through an advocate."
        )

    elif any(k in q for k in ["divorce", "marriage", "wife", "husband", "maintenance", "alimony", "custody", "domestic violence"]):
        return (
            f"⚖️ LEGAL ADVISORY: FAMILY LAW & MATRIMONIAL PROCEEDINGS ({j.upper()})\n\n"
            f"Query: \"{question}\"\n\n"
            "1. APPLICABLE STATUTES:\n"
            "• Hindu Marriage Act, 1955 (HMA) / Special Marriage Act, 1954.\n"
            "• Section 144 BNSS [formerly Section 125 CrPC - Order for maintenance of wives, children and parents].\n"
            "• Protection of Women from Domestic Violence Act, 2005 (PWDVA).\n\n"
            "2. DIVORCE PROCEDURES:\n"
            "• Mutual Consent Divorce (Section 13B HMA): Requires joint petition, settlement of alimony & custody. Mandatory 6-month cooling period can be waived under Supreme Court precedent (Amardeep Singh v. Harveen Kaur).\n"
            "• Contested Divorce (Section 13 HMA): Requires proving statutory grounds such as cruelty, desertion (2+ years), adultery, or conversion.\n\n"
            "3. MAINTENANCE & ALIMONY:\n"
            "• Assessed based on spouse standard of living, financial assets, income affidavits, and dependent children needs.\n\n"
            "Disclaimer: Educational guidance. Matrimonial matters require compassionate and strategic family legal counsel."
        )

    elif any(k in q for k in ["rti", "information", "exam paper", "marksheet", "public record"]):
        return (
            f"⚖️ LEGAL ADVISORY: RIGHT TO INFORMATION (RTI) ({j.upper()})\n\n"
            f"Query: \"{question}\"\n\n"
            "1. APPLICABLE STATUTE:\n"
            "• Right to Information Act, 2005 (RTI Act).\n\n"
            "2. KEY RULES & TIMELINES:\n"
            "• Application Fee: Nominal fee of ₹10 (cash, demand draft, IPO, or online via rtionline.gov.in).\n"
            "• Statutory Response Window: 30 days for general queries; 48 hours if related to life and liberty of an individual.\n"
            "• Examination Answer Sheets: Supreme Court ruled in CBSE v. Aditya Bandopadhyay that students have a statutory right to inspect and obtain copies of evaluated answer sheets under the RTI Act.\n\n"
            "3. APPELLATE PROCEDURE:\n"
            "• First Appeal: If reply is delayed or denied, appeal to First Appellate Authority (FAA) within 30 days.\n"
            "• Second Appeal: File second appeal before Central/State Information Commission (CIC/SIC) within 90 days. Penalty of ₹250/day up to ₹25,000 can be levied on non-compliant Public Information Officers.\n\n"
            "Disclaimer: Educational guidance only."
        )

    else:
        return (
            f"⚖️ LEGAL ADVISORY: GENERAL LEGAL EVALUATION ({j.upper()})\n\n"
            f"Query: \"{question}\"\n\n"
            "1. LEGAL CLASSIFICATION & STATUTORY JURISDICTION:\n"
            f"• Matter classified under the civil and criminal statutory jurisprudence of {j}.\n"
            "• Applicable provisions governed by statutory enactments, regulatory directives, and established judicial precedents.\n\n"
            "2. RECOMMENDED STEP-BY-STEP ACTION PLAN:\n"
            "• Step 1: Issue Formal Legal Demand / Notice — Articulate specific legal grievances, statutory grounds, and a reasonable cure period (typically 15 to 30 days).\n"
            "• Step 2: Assemble Chronological Evidence — Compile agreements, invoices, written communications, bank transcripts, and notices in chronological order.\n"
            "• Step 3: Appropriate Forum Selection — Determine whether the dispute warrants civil litigation, commercial arbitration, consumer dispute commission, or regulatory authority intervention.\n"
            "• Step 4: Engage Competent Counsel — Initiate proceedings through a licensed advocate admitted to the relevant High Court / Bar Association.\n\n"
            "3. LIMITATION ACT PRECAUTION:\n"
            "• Ensure claims are initiated within the statutory limitation period under the Limitation Act, 1963 (typically 3 years for debt recovery and breach of contract).\n\n"
            "Disclaimer: This guidance is for educational awareness and does not constitute formal legal counsel."
        )


def generate_answer(question: str, jurisdiction: str):
    client = build_ai_client()
    model = os.getenv("LLM_MODEL", "").strip()
    if not client or not model:
        return generate_legal_intelligence_response(question, jurisdiction), "demo", []

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
