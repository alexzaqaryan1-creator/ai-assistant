import os
import uuid
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from docx import Document as DocxDocument
from pypdf import PdfReader
from groq import Groq, APIStatusError, APIConnectionError

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", os.urandom(24).hex())
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "40 per hour"],
    storage_uri="memory://",
)

import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"
MAX_DOC_CHARS = 28_000
MAX_HISTORY_TURNS = 6

DOCUMENTS: dict[str, dict] = {}

APP_PASSWORD = os.environ.get("APP_PASSWORD", "").strip()


def _require_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not APP_PASSWORD:
            return view(*args, **kwargs)
        auth = request.authorization
        if not auth or auth.password != APP_PASSWORD:
            return Response(
                "Authentication required.",
                401,
                {"WWW-Authenticate": 'Basic realm="Doc Assistant"'},
            )
        return view(*args, **kwargs)
    return wrapped


def extract_text(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".txt" or ext == ".md":
        return data.decode("utf-8", errors="replace")
    if ext == ".pdf":
        from io import BytesIO
        reader = PdfReader(BytesIO(data))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    if ext == ".docx":
        from io import BytesIO
        doc = DocxDocument(BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError(f"Unsupported file type: {ext}")


@app.route("/")
@_require_auth
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
@_require_auth
@limiter.limit("10 per hour")
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    try:
        data = file.read()
        text = extract_text(file.filename, data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Could not read file: {e}"}), 400

    if not text.strip():
        return jsonify({"error": "Document appears to be empty"}), 400

    truncated = False
    if len(text) > MAX_DOC_CHARS:
        text = text[:MAX_DOC_CHARS]
        truncated = True

    doc_id = uuid.uuid4().hex
    DOCUMENTS[doc_id] = {
        "filename": file.filename,
        "text": text,
        "history": [],
    }
    session["doc_id"] = doc_id

    return jsonify({
        "filename": file.filename,
        "chars": len(text),
        "truncated": truncated,
        "preview": text[:300] + ("..." if len(text) > 300 else ""),
    })


@app.route("/chat", methods=["POST"])
@_require_auth
@limiter.limit("30 per hour")
def chat():
    doc_id = session.get("doc_id")
    if not doc_id or doc_id not in DOCUMENTS:
        return jsonify({"error": "Please upload a document first."}), 400

    payload = request.get_json() or {}
    question = (payload.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Empty question"}), 400

    doc = DOCUMENTS[doc_id]

    system_prompt = (
        "You are a helpful assistant that answers questions based on "
        "the document the user has uploaded. Ground every answer in the "
        "document content. If the answer is not in the document, say so "
        "clearly. Reply in the same language as the user's question. Be "
        "concise and specific; quote short relevant excerpts when useful.\n\n"
        f"Document filename: {doc['filename']}\n\n"
        f"=== DOCUMENT START ===\n{doc['text']}\n=== DOCUMENT END ==="
    )

    messages = (
        [{"role": "system", "content": system_prompt}]
        + list(doc["history"])
        + [{"role": "user", "content": question}]
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=1024,
            temperature=0.3,
        )
    except APIStatusError as e:
        if e.status_code == 413 or "rate_limit" in str(e).lower():
            return jsonify({
                "error": "The document + chat is too big for the free-tier model in one minute. Wait 60 seconds and try again, or upload a shorter document."
            }), 429
        return jsonify({"error": f"API error: {e.message}"}), 502
    except APIConnectionError:
        return jsonify({"error": "Network error contacting the model."}), 502

    answer = response.choices[0].message.content or ""

    doc["history"].append({"role": "user", "content": question})
    doc["history"].append({"role": "assistant", "content": answer})

    max_messages = MAX_HISTORY_TURNS * 2
    if len(doc["history"]) > max_messages:
        doc["history"] = doc["history"][-max_messages:]

    return jsonify({"answer": answer})


@app.route("/reset", methods=["POST"])
@_require_auth
def reset():
    doc_id = session.pop("doc_id", None)
    if doc_id:
        DOCUMENTS.pop(doc_id, None)
    return jsonify({"ok": True})


@app.route("/healthz")
def healthz():
    return {"ok": True}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
