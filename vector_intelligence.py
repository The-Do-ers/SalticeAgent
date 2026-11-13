"""
Vector Intelligence Layer for Saltice Agent
============================================
Powered by LangChain + FAISS + Google Gemini Embeddings

Capabilities:
1. Workspace Code RAG — Semantically index all Python/JS/HTML/MD files in cwd
   and answer "find code that does X" style queries with real similarity scores.
2. Skills Vector Search — Upgrade keyword-based skill matching to cosine-similarity
   embedding search for much better intent-to-skill mapping.
3. Session Memory RAG — Embed and recall past conversation turns so the agent
   never loses context across long sessions.
4. Graceful Degradation — If langchain/faiss not installed, falls back to no-op
   silently so existing code is never broken.

Integration Points:
  - tools.py       → workspace_vector_search() replaces cloudflare_semantic_search when offline
  - skills.py      → SKILL_MANAGER.find_relevant_skills() augmented with vector scores
  - context_manager.py → session_memory_search() for RAG over past turns
"""

import os
import sys
import json
import hashlib
import time
import threading
from typing import List, Dict, Any, Optional, Tuple

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Lazy import guard ────────────────────────────────────────────────────────
_LANGCHAIN_OK = False
_FAISS_OK = False
_EMBEDDINGS = None
_FAISS_CLASS = None
_DOCUMENT_CLASS = None

def _try_import_langchain():
    global _LANGCHAIN_OK, _FAISS_OK, _EMBEDDINGS, _FAISS_CLASS, _DOCUMENT_CLASS
    if _LANGCHAIN_OK:
        return True
    try:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from langchain_community.vectorstores import FAISS
        from langchain_core.documents import Document

        from dotenv import load_dotenv
        load_dotenv(os.path.join(AGENT_DIR, ".env"))
        api_key = os.getenv("GEMINI_API_KEY", "")

        _EMBEDDINGS = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-2",
            google_api_key=api_key,
            task_type="retrieval_document"
        )
        _FAISS_CLASS = FAISS
        _DOCUMENT_CLASS = Document
        _LANGCHAIN_OK = True
        _FAISS_OK = True
        return True
    except Exception as e:
        # Silently fall back — never break the agent
        return False


# ─── Paths ────────────────────────────────────────────────────────────────────
_VECTOR_STORE_DIR = os.path.join(AGENT_DIR, ".saltice", "vector_stores")
_WORKSPACE_INDEX_PATH = os.path.join(_VECTOR_STORE_DIR, "workspace_code")
_SKILLS_INDEX_PATH    = os.path.join(_VECTOR_STORE_DIR, "skills_catalog")
_SESSION_INDEX_PATH   = os.path.join(_VECTOR_STORE_DIR, "session_memory")
_MANIFEST_PATH        = os.path.join(_VECTOR_STORE_DIR, "index_manifest.json")

os.makedirs(_VECTOR_STORE_DIR, exist_ok=True)

# ─── Manifest: track file hashes to avoid unnecessary re-indexing ─────────────
def _load_manifest() -> Dict[str, str]:
    try:
        with open(_MANIFEST_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_manifest(manifest: Dict[str, str]):
    try:
        with open(_MANIFEST_PATH, "w") as f:
            json.dump(manifest, f, indent=2)
    except Exception:
        pass

def _file_hash(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""


# ─── Workspace Code Indexer ───────────────────────────────────────────────────
_INDEXABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".md",
    ".json", ".yaml", ".yml", ".txt", ".env"
}
_SKIP_DIRS = {
    "__pycache__", "node_modules", ".git", ".saltice", "artifacts",
    "diagnostics", "rate_limited_queue", "saltice_agent.egg-info",
    ".repo_cache", "web_ui", ".agents"
}
_MAX_FILE_SIZE = 64 * 1024   # 64 KB per file
_MAX_CHUNK_LEN = 800          # characters per chunk


def _chunk_text(text: str, source: str) -> List[Any]:
    """Split text into overlapping chunks and return Document objects."""
    if not _DOCUMENT_CLASS:
        return []
    chunks = []
    lines = text.split("\n")
    current_chunk_lines = []
    current_len = 0
    for line in lines:
        current_chunk_lines.append(line)
        current_len += len(line) + 1
        if current_len >= _MAX_CHUNK_LEN:
            chunk_text = "\n".join(current_chunk_lines).strip()
            if chunk_text:
                chunks.append(_DOCUMENT_CLASS(
                    page_content=chunk_text,
                    metadata={"source": source, "type": "code"}
                ))
            # Overlap: keep last 8 lines
            current_chunk_lines = current_chunk_lines[-8:]
            current_len = sum(len(l) + 1 for l in current_chunk_lines)
    remainder = "\n".join(current_chunk_lines).strip()
    if remainder and len(remainder) > 50:
        chunks.append(_DOCUMENT_CLASS(
            page_content=remainder,
            metadata={"source": source, "type": "code"}
        ))
    return chunks


def _embed_with_backoff(docs: List[Any], max_retries: int = 5) -> Optional[Any]:
    """
    Embed a list of documents with exponential backoff for rate-limit errors.
    Returns a FAISS vector store or None on failure.
    """
    import time as _time
    for attempt in range(max_retries):
        try:
            return _FAISS_CLASS.from_documents(docs, _EMBEDDINGS)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                wait_sec = (2 ** attempt) * 8  # 8, 16, 32, 64, 128 seconds
                # Extract retry delay from error message if available
                import re as _re
                delay_match = _re.search(r"retry.*?(\d+(?:\.\d+)?)\s*s", err_str, _re.IGNORECASE)
                if delay_match:
                    wait_sec = max(wait_sec, float(delay_match.group(1)) + 2)
                print(f"[VecIntel] Rate limited. Waiting {wait_sec:.0f}s before retry {attempt+1}/{max_retries}...")
                _time.sleep(wait_sec)
            else:
                raise  # Non-rate-limit errors: re-raise immediately
    return None


def build_workspace_index(workspace_dir: str, force: bool = False, max_files: int = 30) -> Tuple[bool, str]:
    """
    Crawl workspace_dir, embed code files, save FAISS index.
    Returns (success, message).
    Skips unchanged files using MD5 manifest.
    Batches embedding to stay within free tier rate limits.
    max_files: limit files indexed per run to avoid quota exhaustion (default 30).
    """
    if not _try_import_langchain():
        return False, "LangChain/FAISS not available. Run: pip install langchain langchain-community langchain-google-genai faiss-cpu"

    manifest = _load_manifest()
    new_docs = []
    changed_files = []
    skipped = 0

    # Priority: Python files first (most useful for agent), then others
    priority_exts = [".py", ".md"]
    low_priority_exts = _INDEXABLE_EXTENSIONS - set(priority_exts)

    def collect_files(workspace_dir, priority_first=True):
        collected = []
        for root, dirs, files in os.walk(workspace_dir):
            dirs[:] = [d for d in dirs if d not in _SKIP_DIRS and not d.startswith(".")]
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in _INDEXABLE_EXTENSIONS:
                    continue
                fpath = os.path.join(root, fname)
                priority = 0 if ext in priority_exts else 1
                collected.append((priority, fpath))
        if priority_first:
            collected.sort(key=lambda x: x[0])
        return [fp for _, fp in collected]

    all_files = collect_files(workspace_dir)

    for fpath in all_files:
        if len(changed_files) >= max_files:
            break
        rel_path = os.path.relpath(fpath, workspace_dir)
        try:
            fsize = os.path.getsize(fpath)
            if fsize > _MAX_FILE_SIZE or fsize == 0:
                continue
            fhash = _file_hash(fpath)
            manifest_key = f"ws:{rel_path}"
            if not force and manifest.get(manifest_key) == fhash:
                skipped += 1
                continue
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
            if not content:
                continue
            chunks = _chunk_text(content, rel_path)
            new_docs.extend(chunks[:3])  # Max 3 chunks per file to control volume
            manifest[manifest_key] = fhash
            changed_files.append(rel_path)
        except Exception:
            continue

    if not new_docs:
        return True, f"Workspace index up to date. {skipped} files unchanged."

    # Batch embedding: process in small batches to avoid rate limits
    BATCH_SIZE = 20  # Chunks per embedding call
    import time as _time

    try:
        combined_store = None
        for batch_start in range(0, len(new_docs), BATCH_SIZE):
            batch = new_docs[batch_start:batch_start + BATCH_SIZE]
            store = _embed_with_backoff(batch)
            if store is None:
                return False, f"Embedding failed after retries at chunk {batch_start}"
            if combined_store is None:
                combined_store = store
            else:
                combined_store.merge_from(store)
            if batch_start + BATCH_SIZE < len(new_docs):
                _time.sleep(2)  # Small pause between batches

        # Merge with existing index if present
        if os.path.exists(_WORKSPACE_INDEX_PATH) and not force and combined_store:
            try:
                existing = _FAISS_CLASS.load_local(
                    _WORKSPACE_INDEX_PATH, _EMBEDDINGS,
                    allow_dangerous_deserialization=True
                )
                existing.merge_from(combined_store)
                existing.save_local(_WORKSPACE_INDEX_PATH)
            except Exception:
                combined_store.save_local(_WORKSPACE_INDEX_PATH)
        elif combined_store:
            combined_store.save_local(_WORKSPACE_INDEX_PATH)

        _save_manifest(manifest)
        remaining = max(0, len(all_files) - len(changed_files) - skipped)
        note = f" ({remaining} files deferred to next run)" if remaining > 0 else ""
        return True, f"Indexed {len(new_docs)} chunks from {len(changed_files)} files. ({skipped} unchanged){note}"
    except Exception as e:
        return False, f"Indexing failed: {e}"



def workspace_vector_search(query: str, workspace_dir: str, top_k: int = 5) -> str:
    """
    Semantic similarity search over indexed workspace files.
    Returns formatted string with matching code snippets and file paths.
    Falls back to empty string if index not built or langchain unavailable.
    """
    if not _try_import_langchain():
        return ""
    if not os.path.exists(_WORKSPACE_INDEX_PATH):
        # Auto-trigger background index build
        _async_build_workspace_index(workspace_dir)
        return "[Vector index building in background. Try again in a moment.]"
    try:
        store = _FAISS_CLASS.load_local(
            _WORKSPACE_INDEX_PATH,
            _EMBEDDINGS,
            allow_dangerous_deserialization=True
        )
        results = store.similarity_search_with_score(query, k=top_k)
        if not results:
            return ""
        lines = [f"🔍 **Vector Search Results** (query: `{query[:60]}`)"]
        for doc, score in results:
            src = doc.metadata.get("source", "unknown")
            snippet = doc.page_content[:400].replace("\n", "\n  ")
            lines.append(f"\n📄 **{src}** [similarity: {1 - score:.3f}]\n```\n  {snippet}\n```")
        return "\n".join(lines)
    except Exception as e:
        return f"[Vector search error: {e}]"


def _async_build_workspace_index(workspace_dir: str):
    """Trigger workspace indexing in background thread."""
    def _build():
        _try_import_langchain()
        build_workspace_index(workspace_dir)
    t = threading.Thread(target=_build, daemon=True)
    t.start()


# ─── Skills Vector Index ──────────────────────────────────────────────────────

def build_skills_index(skills_dict: Dict[str, Any], force: bool = False) -> Tuple[bool, str]:
    """
    Embed all skills (name + description + when_to_use) and build FAISS index.
    skills_dict: {name: Skill} from SKILL_MANAGER.skills
    """
    if not _try_import_langchain():
        return False, "LangChain not available"

    manifest = _load_manifest()
    docs = []
    # Hash all skill names+descriptions as a combined fingerprint
    all_names = sorted(skills_dict.keys())
    combined_hash = hashlib.md5("|".join(all_names).encode()).hexdigest()
    if not force and manifest.get("skills_hash") == combined_hash and os.path.exists(_SKILLS_INDEX_PATH):
        return True, f"Skills index up to date ({len(skills_dict)} skills)."

    for name, skill in skills_dict.items():
        when_to_use_text = " | ".join(getattr(skill, "when_to_use", [])[:5])
        content = f"SKILL: {name}\nDESCRIPTION: {skill.description}\nUSE WHEN: {when_to_use_text}\nCATEGORY: {skill.category}"
        docs.append(_DOCUMENT_CLASS(
            page_content=content,
            metadata={"skill_name": name, "category": getattr(skill, "category", ""), "type": "skill"}
        ))

    if not docs:
        return False, "No skills found to index"

    try:
        store = _FAISS_CLASS.from_documents(docs, _EMBEDDINGS)
        store.save_local(_SKILLS_INDEX_PATH)
        manifest["skills_hash"] = combined_hash
        _save_manifest(manifest)
        return True, f"Skills index built with {len(docs)} entries."
    except Exception as e:
        return False, f"Skills indexing failed: {e}"


def find_skills_by_vector(query: str, top_k: int = 3) -> List[Tuple[str, float]]:
    """
    Vector-based skill matching. Returns list of (skill_name, score) tuples.
    Returns empty list if unavailable.
    """
    if not _try_import_langchain():
        return []
    if not os.path.exists(_SKILLS_INDEX_PATH):
        return []
    try:
        store = _FAISS_CLASS.load_local(
            _SKILLS_INDEX_PATH,
            _EMBEDDINGS,
            allow_dangerous_deserialization=True
        )
        results = store.similarity_search_with_score(query, k=top_k)
        skill_scores = []
        for doc, dist_score in results:
            skill_name = doc.metadata.get("skill_name", "")
            similarity = max(0.0, 1.0 - dist_score)  # Convert L2 dist to 0-1 similarity
            if skill_name and similarity > 0.3:
                skill_scores.append((skill_name, round(similarity, 3)))
        return skill_scores
    except Exception:
        return []


# ─── Session Memory RAG ───────────────────────────────────────────────────────

_session_lock = threading.Lock()

def embed_session_turn(session_id: str, role: str, content: str, turn_index: int):
    """
    Embed a single conversation turn into the session memory index.
    Call this after every user/assistant exchange.
    Non-blocking (runs in background thread).
    """
    def _embed():
        if not _try_import_langchain():
            return
        if not content or len(content.strip()) < 20:
            return
        snippet = content[:1000]
        doc = _DOCUMENT_CLASS(
            page_content=snippet,
            metadata={
                "session_id": session_id,
                "role": role,
                "turn": turn_index,
                "timestamp": time.time()
            }
        )
        with _session_lock:
            try:
                if os.path.exists(_SESSION_INDEX_PATH):
                    store = _FAISS_CLASS.load_local(
                        _SESSION_INDEX_PATH,
                        _EMBEDDINGS,
                        allow_dangerous_deserialization=True
                    )
                    store.add_documents([doc])
                else:
                    store = _FAISS_CLASS.from_documents([doc], _EMBEDDINGS)
                store.save_local(_SESSION_INDEX_PATH)
            except Exception:
                pass

    t = threading.Thread(target=_embed, daemon=True)
    t.start()


def search_session_memory(query: str, top_k: int = 3, session_id: Optional[str] = None) -> str:
    """
    Search past conversation turns for relevant context.
    Returns a formatted string with the most relevant past exchanges.
    """
    if not _try_import_langchain():
        return ""
    if not os.path.exists(_SESSION_INDEX_PATH):
        return ""
    try:
        store = _FAISS_CLASS.load_local(
            _SESSION_INDEX_PATH,
            _EMBEDDINGS,
            allow_dangerous_deserialization=True
        )
        filter_dict = {"session_id": session_id} if session_id else None
        results = store.similarity_search_with_score(query, k=top_k * 2)

        lines = []
        seen = set()
        for doc, dist in results:
            if session_id and doc.metadata.get("session_id") != session_id:
                continue
            sim = max(0.0, 1.0 - dist)
            if sim < 0.4:
                continue
            content_key = doc.page_content[:80]
            if content_key in seen:
                continue
            seen.add(content_key)
            role = doc.metadata.get("role", "?")
            turn = doc.metadata.get("turn", "?")
            snippet = doc.page_content[:300]
            lines.append(f"[Turn {turn} | {role}] {snippet}")
            if len(lines) >= top_k:
                break

        if not lines:
            return ""
        return "📚 **Relevant Past Context:**\n" + "\n---\n".join(lines)
    except Exception:
        return ""


# ─── Status & Health ──────────────────────────────────────────────────────────

def get_vector_status() -> Dict[str, Any]:
    """Returns current status of all vector indexes for display in UI."""
    langchain_ok = _try_import_langchain()
    status = {
        "langchain_available": langchain_ok,
        "workspace_index_exists": os.path.exists(_WORKSPACE_INDEX_PATH),
        "skills_index_exists": os.path.exists(_SKILLS_INDEX_PATH),
        "session_index_exists": os.path.exists(_SESSION_INDEX_PATH),
        "index_dir": _VECTOR_STORE_DIR,
    }
    if langchain_ok:
        status["embedding_model"] = "models/gemini-embedding-2"
        status["vector_backend"] = "FAISS (local, offline-capable after first build)"
    return status


def index_workspace_async(workspace_dir: str):
    """Public entry point: kick off workspace indexing in background."""
    _async_build_workspace_index(workspace_dir)
