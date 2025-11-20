# plagiarism_server.py
"""
FastAPI local plagiarism checker using datasketch MinHash + LSH.
Supports .txt, .pdf (multiple strategies), .docx (python-docx), .doc (textract or antiword), .csv

Install dependencies (see instructions below).
"""

import os
import io
import json
import pickle
import shutil
import subprocess
import logging
from typing import List, Dict, Optional
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from datasketch import MinHash, MinHashLSH

# Text extraction libraries
from pdfminer.high_level import extract_text as extract_text_pdfminer
from PyPDF2 import PdfReader
try:
    import pdfplumber
    HAVE_PDFPLUMBER = True
except Exception:
    HAVE_PDFPLUMBER = False

import docx
import pandas as pd

# Optional textract import (may have heavy system deps)
try:
    import textract
    HAVE_TEXTRACT = True
except Exception:
    HAVE_TEXTRACT = False

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("plagiarism_server")

# ---------- Configuration ----------
CORPUS_DIR = "corpus"               # saved raw files & json metadata
INDEX_FILE = "lsh_index.pkl"        # persisted LSH and metadata

SHINGLE_SIZE = 5      # number of words per shingle (tuneable)
NUM_PERM = 128        # MinHash permutations
LSH_THRESHOLD = 0.5   # LSH threshold
# -----------------------------------

app = FastAPI(title="TextGuard Local Plagiarism (MinHash+LSH)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local dev - restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory index structures
lsh: MinHashLSH = None
metadata: Dict[str, Dict] = {}   # doc_id -> {name, path, words_count, shingles_count}
minhash_store: Dict[str, MinHash] = {}  # doc_id -> MinHash object


# ----------------- Utilities -----------------
def ensure_dirs():
    os.makedirs(CORPUS_DIR, exist_ok=True)


def extract_text_from_docx(file_path: str) -> str:
    try:
        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs]
        return "\n".join(paragraphs)
    except Exception as e:
        logger.exception("python-docx failed")
        return ""


def extract_text_from_csv_bytes(data: bytes, filename: str) -> str:
    """
    Read CSV into pandas and join all cells into a single text blob.
    Handles various encodings by trying utf-8 then latin-1.
    """
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(io.BytesIO(data), encoding=enc, engine='python', dtype=str, low_memory=False)
            # convert all to string, fill NaN, join by space
            text = " ".join(df.fillna("").astype(str).apply(lambda row: " ".join(row.values), axis=1).tolist())
            return text
        except Exception as e:
            logger.debug("CSV read failed with encoding %s: %s", enc, e)
            continue
    return ""


def extract_text_from_pdf_bytes(data: bytes) -> str:
    """
    Robust PDF extraction with multiple fallbacks:
      1) pdfminer.six (extract_text)
      2) PyPDF2 (page by page)
      3) pdfplumber (if installed)
    """
    # 1) pdfminer
    try:
        with io.BytesIO(data) as f:
            text = extract_text_pdfminer(f)
        if text and text.strip():
            logger.debug("PDF parsed by pdfminer")
            return text
    except Exception as e:
        logger.debug("pdfminer failed: %s", e)

    # 2) PyPDF2
    try:
        with io.BytesIO(data) as f:
            reader = PdfReader(f)
            pages = []
            for p in reader.pages:
                try:
                    pages.append(p.extract_text() or "")
                except Exception:
                    pages.append("")
            text = "\n".join(pages)
        if text and text.strip():
            logger.debug("PDF parsed by PyPDF2")
            return text
    except Exception as e:
        logger.debug("PyPDF2 failed: %s", e)

    # 3) pdfplumber (optional)
    if HAVE_PDFPLUMBER:
        try:
            with io.BytesIO(data) as f:
                with pdfplumber.open(f) as pdf:
                    pages = [p.extract_text() or "" for p in pdf.pages]
                    text = "\n".join(pages)
            if text and text.strip():
                logger.debug("PDF parsed by pdfplumber")
                return text
        except Exception as e:
            logger.debug("pdfplumber failed: %s", e)

    # As a last resort return empty (caller will handle)
    return ""


def extract_text_from_doc_bytes(filename: str, data: bytes) -> str:
    """
    Try to extract text from old .doc files.
    Strategies:
      1) textract (if installed)
      2) antiword command-line (if present)
    """
    name = filename.lower()
    # 1) textract (python wrapper)
    if HAVE_TEXTRACT:
        try:
            text = textract.process(filename, input_encoding='utf-8') if False else textract.process(io.BytesIO(data))
            if isinstance(text, bytes):
                return text.decode(errors="ignore")
            return str(text)
        except Exception as e:
            logger.debug("textract failed: %s", e)

    # 2) antiword (external)
    try:
        # write to temp file and call antiword
        tmp = os.path.join(CORPUS_DIR, f"tmp_{os.getpid()}.doc")
        with open(tmp, "wb") as t:
            t.write(data)
        try:
            # antiword prints to stdout
            res = subprocess.run(["antiword", tmp], capture_output=True, text=True, timeout=15)
            if res.returncode == 0 and res.stdout:
                return res.stdout
        except FileNotFoundError:
            logger.debug("antiword not installed")
        except Exception as e:
            logger.debug("antiword call failed: %s", e)
        finally:
            try:
                os.remove(tmp)
            except Exception:
                pass
    except Exception:
        logger.exception("Failed to use antiword fallback for .doc")

    # nothing worked
    return ""


def extract_text_from_file_bytes(filename: str, data: bytes) -> str:
    """
    Central extraction function that dispatches based on extension.
    Supports .txt, .pdf, .docx, .doc, .csv
    """
    name = filename.lower().strip()
    try:
        if name.endswith(".txt"):
            # try utf-8 then fallback
            try:
                return data.decode("utf-8")
            except Exception:
                return data.decode("latin-1", errors="ignore")
        elif name.endswith(".pdf"):
            return extract_text_from_pdf_bytes(data)
        elif name.endswith(".docx"):
            # write tmp and use python-docx
            tmp = os.path.join(CORPUS_DIR, f"tmp_{os.getpid()}.docx")
            with open(tmp, "wb") as t:
                t.write(data)
            try:
                return extract_text_from_docx(tmp)
            finally:
                try:
                    os.remove(tmp)
                except Exception:
                    pass
        elif name.endswith(".doc"):
            return extract_text_from_doc_bytes(filename, data)
        elif name.endswith(".csv"):
            return extract_text_from_csv_bytes(data, filename)
        else:
            # last resort: attempt text decode
            try:
                return data.decode("utf-8", errors="ignore")
            except Exception:
                return data.decode("latin-1", errors="ignore")
    except Exception as e:
        logger.exception("extract_text_from_file_bytes failed for %s: %s", filename, e)
        return ""


def tokenize(text: str) -> List[str]:
    import re
    text = (text or "").lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    tokens = [t for t in text.split(" ") if t]
    return tokens


def shingles_from_tokens(tokens: List[str], k: int) -> List[str]:
    if len(tokens) == 0:
        return []
    if len(tokens) <= k:
        return [" ".join(tokens)]
    return [" ".join(tokens[i:i+k]) for i in range(len(tokens)-k+1)]


def minhash_from_shingles(shingles: List[str]) -> MinHash:
    m = MinHash(num_perm=NUM_PERM)
    for s in shingles:
        try:
            m.update(s.encode("utf8"))
        except Exception:
            # ignore problematic shingles
            continue
    return m


def compute_jaccard(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    inter = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return inter / union if union else 0.0


def persist_index():
    global lsh, metadata, minhash_store
    try:
        with open(INDEX_FILE, "wb") as f:
            pickle.dump({
                "lsh": lsh,
                "minhash_store": minhash_store,
                "metadata": metadata
            }, f)
    except Exception:
        logger.exception("Failed to persist index")


def load_index():
    global lsh, metadata, minhash_store
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, "rb") as f:
                data = pickle.load(f)
                lsh = data.get("lsh")
                minhash_store = data.get("minhash_store", {})
                metadata = data.get("metadata", {})
                logger.info("Loaded index with %d docs", len(metadata))
        except Exception:
            logger.exception("Failed to load existing index, creating new one")
            lsh = MinHashLSH(threshold=LSH_THRESHOLD, num_perm=NUM_PERM)
            metadata = {}
            minhash_store = {}
    else:
        lsh = MinHashLSH(threshold=LSH_THRESHOLD, num_perm=NUM_PERM)
        metadata = {}
        minhash_store = {}


# ----------------- API endpoints -----------------
@app.on_event("startup")
def startup():
    ensure_dirs()
    load_index()


@app.post("/api/index-file")
async def index_file(file: UploadFile = File(...)):
    """
    Upload a file to index it into the local corpus and LSH index.
    Accepts .txt, .pdf, .docx, .doc, .csv. Returns doc_id and stats.
    """
    content = await file.read()
    text = extract_text_from_file_bytes(file.filename, content)
    if not text or not text.strip():
        logger.warning("Failed to extract text for file: %s", file.filename)
        return JSONResponse({"ok": False, "error": f"Could not extract text from file: {file.filename}. Try converting to .txt or installing antiword/textract for .doc."}, status_code=400)

    tokens = tokenize(text)
    shingles = shingles_from_tokens(tokens, SHINGLE_SIZE)
    doc_id = f"doc_{len(metadata)+1}"

    # save original file
    safe_name = f"{doc_id}__{file.filename}"
    path = os.path.join(CORPUS_DIR, safe_name)
    with open(path, "wb") as f:
        f.write(content)

    # minhash & index
    m = minhash_from_shingles(shingles)
    global lsh
    if lsh is None:
        lsh = MinHashLSH(threshold=LSH_THRESHOLD, num_perm=NUM_PERM)
    lsh.insert(doc_id, m)
    minhash_store[doc_id] = m

    # store metadata
    metadata[doc_id] = {
        "filename": file.filename,
        "path": path,
        "words_count": len(tokens),
        "shingles_count": len(set(shingles)),
    }

    persist_index()
    logger.info("Indexed %s as %s (words=%d)", file.filename, doc_id, len(tokens))
    return {"ok": True, "doc_id": doc_id, "filename": file.filename, "words": len(tokens), "shingles": len(set(shingles))}


@app.post("/api/index-text")
async def index_text(title: str = Form(...), text: str = Form(...)):
    if not text.strip():
        return JSONResponse({"ok": False, "error": "Empty text"}, status_code=400)

    tokens = tokenize(text)
    shingles = shingles_from_tokens(tokens, SHINGLE_SIZE)
    doc_id = f"doc_{len(metadata)+1}"
    path = os.path.join(CORPUS_DIR, f"{doc_id}__{title}.txt")
    with open(path, "w", encoding="utf8") as f:
        f.write(text)

    m = minhash_from_shingles(shingles)
    global lsh
    if lsh is None:
        lsh = MinHashLSH(threshold=LSH_THRESHOLD, num_perm=NUM_PERM)
    lsh.insert(doc_id, m)
    minhash_store[doc_id] = m

    metadata[doc_id] = {
        "filename": title,
        "path": path,
        "words_count": len(tokens),
        "shingles_count": len(set(shingles)),
    }

    persist_index()
    return {"ok": True, "doc_id": doc_id, "filename": title, "words": len(tokens), "shingles": len(set(shingles))}


@app.post("/api/check-text")
async def check_text(text: str = Form(...), top_k: int = Form(5)):
    if not text.strip():
        return JSONResponse({"ok": False, "error": "Empty text"}, status_code=400)

    tokens = tokenize(text)
    shingles = shingles_from_tokens(tokens, SHINGLE_SIZE)
    query_m = minhash_from_shingles(shingles)

    global lsh
    if lsh is None:
        return {"ok": True, "matches": []}

    candidates = lsh.query(query_m)
    results = []

    for doc_id in candidates:
        meta = metadata.get(doc_id)
        if not meta:
            continue
        try:
            with open(meta["path"], "rb") as fh:
                data = fh.read()
            raw = extract_text_from_file_bytes(meta["filename"], data)
            tokens2 = tokenize(raw)
            shingles2 = set(shingles_from_tokens(tokens2, SHINGLE_SIZE))
        except Exception:
            shingles2 = set()
        sim = compute_jaccard(set(shingles), shingles2)
        results.append({
            "doc_id": doc_id,
            "filename": meta.get("filename"),
            "words": meta.get("words_count"),
            "shingles": meta.get("shingles_count"),
            "jaccard": round(sim, 5),
            "percent": round(sim * 100, 2)
        })

    results.sort(key=lambda x: x["jaccard"], reverse=True)
    return {"ok": True, "matches": results[:top_k], "candidates_count": len(candidates)}


@app.post("/api/check-file")
async def check_file(file: UploadFile = File(...), top_k: int = Form(5)):
    content = await file.read()
    text = extract_text_from_file_bytes(file.filename, content)
    if not text or not text.strip():
        logger.warning("Could not extract text for check-file: %s", file.filename)
        return JSONResponse({"ok": False, "error": "Could not extract text from file"}, status_code=400)

    tokens = tokenize(text)
    shingles = shingles_from_tokens(tokens, SHINGLE_SIZE)
    query_m = minhash_from_shingles(shingles)

    global lsh
    if lsh is None:
        return {"ok": True, "matches": [], "candidates_count": 0}

    candidates = lsh.query(query_m)
    results = []
    for doc_id in candidates:
        meta = metadata.get(doc_id)
        if not meta:
            continue
        try:
            with open(meta["path"], "rb") as fh:
                data = fh.read()
            raw = extract_text_from_file_bytes(meta["filename"], data)
            tokens2 = tokenize(raw)
            shingles2 = set(shingles_from_tokens(tokens2, SHINGLE_SIZE))
        except Exception:
            shingles2 = set()
        sim = compute_jaccard(set(shingles), shingles2)
        results.append({
            "doc_id": doc_id,
            "filename": meta.get("filename"),
            "words": meta.get("words_count"),
            "shingles": meta.get("shingles_count"),
            "jaccard": round(sim, 5),
            "percent": round(sim * 100, 2)
        })
    results.sort(key=lambda x: x["jaccard"], reverse=True)
    return {"ok": True, "matches": results[:top_k], "candidates_count": len(candidates)}


@app.get("/api/list-docs")
async def list_docs():
    return {"ok": True, "docs": metadata}


@app.post("/api/clear-index")
async def clear_index():
    global lsh, metadata, minhash_store
    lsh = MinHashLSH(threshold=LSH_THRESHOLD, num_perm=NUM_PERM)
    metadata = {}
    minhash_store = {}
    try:
        shutil.rmtree(CORPUS_DIR)
    except Exception:
        pass
    ensure_dirs()
    persist_index()
    return {"ok": True}
