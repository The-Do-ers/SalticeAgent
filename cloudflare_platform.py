"""
Cloudflare Full-Stack Platform Integration for Saltice
Equipped with:
1. Cloudflare Pages Deployer (1-click direct upload deployment to *.pages.dev)
2. Cloudflare URL Scanner (Automated security & live DOM inspection)
3. Cloudflare D1 (Edge SQLite database for persistent agent memory & telemetry)
4. Cloudflare Vectorize + Workers AI BGE Embeddings (Semantic code search & RAG)
5. Cloudflare Workers AI DeepSeek-R1 (Deep algorithmic reasoning & self-healing)
"""

import os
import sys
import json
import time
import base64
import hashlib
import requests
try:
    import blake3
except ImportError:
    blake3 = None
from dotenv import load_dotenv

CLI_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(CLI_DIR, ".env"))
load_dotenv()

CF_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip().strip()
CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()

def _get_headers(json_type: bool = True) -> dict:
    h = {"Authorization": f"Bearer {CF_API_TOKEN}"}
    if json_type:
        h["Content-Type"] = "application/json"
    return h


# =========================================================================
# 1. CLOUDFLARE PAGES 1-CLICK DEPLOYER
# =========================================================================
def deploy_to_pages(filepath: str, project_name: str = "saltice-preview") -> tuple[bool, str, str]:
    """
    Directly uploads a single-file HTML app or web project to Cloudflare Pages.
    Returns: (success: bool, message: str, live_url: str)
    """
    if not CF_ACCOUNT_ID or not CF_API_TOKEN:
        return False, "Cloudflare credentials not configured in .env", ""

    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}", ""

    try:
        # Read file content
        with open(filepath, "rb") as f:
            content = f.read()

        b64 = base64.b64encode(content).decode("ascii")
        ext = os.path.splitext(filepath)[1].lstrip(".").lower() or "html"
        if blake3:
            file_hash = blake3.blake3((b64 + ext).encode("utf-8")).hexdigest()[:32]
        else:
            file_hash = hashlib.md5((b64 + ext).encode("utf-8")).hexdigest()[:32]

        # 1. Ensure project exists
        p_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/pages/projects"
        requests.post(p_url, headers=_get_headers(True), json={"name": project_name, "production_branch": "main"})

        # 2. Get upload token JWT
        t_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/pages/projects/{project_name}/upload-token"
        t_res = requests.get(t_url, headers=_get_headers(True), timeout=15)
        if t_res.status_code != 200 or not t_res.json().get("result", {}).get("jwt"):
            return False, f"Failed to acquire Cloudflare upload token ({t_res.status_code}): {t_res.text[:200]}", ""
        jwt = t_res.json()["result"]["jwt"]
        h_jwt = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}

        # 3. Check missing assets
        chk_res = requests.post(
            "https://api.cloudflare.com/client/v4/pages/assets/check-missing",
            headers=h_jwt,
            json={"hashes": [file_hash]},
            timeout=15
        )
        missing = chk_res.json().get("result", []) if chk_res.status_code == 200 else [file_hash]

        # 4. Upload missing asset
        if file_hash in missing:
            payload = [{
                "key": file_hash,
                "value": b64,
                "metadata": {"contentType": "text/html"},
                "base64": True
            }]
            u_res = requests.post(
                "https://api.cloudflare.com/client/v4/pages/assets/upload",
                headers=h_jwt,
                json=payload,
                timeout=30
            )
            if u_res.status_code != 200:
                return False, f"Cloudflare asset upload failed ({u_res.status_code}): {u_res.text[:200]}", ""

        # 5. Upsert hashes
        requests.post(
            "https://api.cloudflare.com/client/v4/pages/assets/upsert-hashes",
            headers=h_jwt,
            json={"hashes": [file_hash]},
            timeout=15
        )

        # 6. Deploy asset via Direct Upload Manifest API
        deploy_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/pages/projects/{project_name}/deployments"
        manifest = json.dumps({"/index.html": file_hash})
        files = {"manifest": (None, manifest)}

        d_res = requests.post(deploy_url, headers=_get_headers(False), files=files, timeout=30)
        if d_res.status_code == 200:
            res = d_res.json().get("result", {})
            live_url = res.get("url") or f"https://{project_name}.pages.dev"
            msg = f"Successfully deployed {os.path.basename(filepath)} to Cloudflare Pages!"
            return True, msg, live_url
        else:
            return False, f"Cloudflare Pages Deployment failed ({d_res.status_code}): {d_res.text[:200]}", ""

    except Exception as e:
        return False, f"Pages deployment error: {str(e)}", ""


# =========================================================================
# 2. CLOUDFLARE URL SCANNER
# =========================================================================
def scan_url(target_url: str) -> dict:
    """
    Submits a public URL to Cloudflare URL Scanner for security and accessibility audit.
    """
    if not CF_ACCOUNT_ID or not CF_API_TOKEN:
        return {"ok": False, "error": "Cloudflare credentials missing"}

    try:
        url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/urlscanner/scan"
        payload = {"url": target_url, "visibility": "public"}
        r = requests.post(url, headers=_get_headers(True), json=payload, timeout=20)
        if r.status_code == 200:
            res = r.json().get("result", {})
            return {
                "ok": True,
                "scan_uuid": res.get("uuid"),
                "url": res.get("url"),
                "message": "Scan initiated. Results available on Cloudflare Security Center."
            }
        return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:150]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =========================================================================
# 3. CLOUDFLARE D1 (EDGE SQLITE PERSISTENCE)
# =========================================================================
D1_DATABASE_NAME = "saltice-db"
_cached_d1_id = None

def _get_or_create_d1_id() -> str:
    global _cached_d1_id
    if _cached_d1_id:
        return _cached_d1_id

    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/d1/database"
    r = requests.get(url, headers=_get_headers(True), timeout=15)
    if r.status_code == 200:
        for db in r.json().get("result", []):
            if db.get("name") == D1_DATABASE_NAME:
                _cached_d1_id = db.get("uuid")
                return _cached_d1_id

    # Create if missing
    r_create = requests.post(url, headers=_get_headers(True), json={"name": D1_DATABASE_NAME}, timeout=15)
    if r_create.status_code in [200, 201]:
        _cached_d1_id = r_create.json().get("result", {}).get("uuid")
        return _cached_d1_id

    return None

def d1_execute_sql(sql: str, params: list = None) -> dict:
    """Execute raw SQL against Cloudflare D1 Edge SQLite database."""
    db_id = _get_or_create_d1_id()
    if not db_id:
        return {"ok": False, "error": "Cannot access or create D1 database"}

    try:
        url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/d1/database/{db_id}/query"
        payload = {"sql": sql, "params": params or []}
        r = requests.post(url, headers=_get_headers(True), json=payload, timeout=15)
        if r.status_code == 200:
            data = r.json()
            results = data.get("result", [{}])[0].get("results", [])
            return {"ok": True, "results": results, "meta": data.get("result", [{}])[0].get("meta", {})}
        return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:150]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# =========================================================================
# 4. CLOUDFLARE WORKERS AI EMBEDDINGS & VECTORIZE (SEMANTIC RAG)
# =========================================================================
def generate_cloudflare_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generates 768-dimensional dense vector embeddings using @cf/baai/bge-base-en-v1.5.
    """
    if not CF_ACCOUNT_ID or not CF_API_TOKEN:
        return []

    try:
        url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/baai/bge-base-en-v1.5"
        r = requests.post(url, headers=_get_headers(True), json={"text": texts}, timeout=25)
        if r.status_code == 200:
            return r.json().get("result", {}).get("data", [])
        return []
    except Exception:
        return []

def semantic_code_search(query: str, search_dir: str = ".") -> list[dict]:
    """
    Local Vector Semantic Code Search:
    Indexes code chunks in search_dir using Cloudflare BGE embeddings,
    computes cosine similarity against the query embedding, and returns the top 5 matches!
    """
    query_embed = generate_cloudflare_embeddings([query])
    if not query_embed:
        return []

    q_vec = query_embed[0]

    # Collect code chunks from workspace
    chunks = []
    supported_exts = {".py", ".js", ".html", ".css", ".md", ".json"}
    for root, _, files in os.walk(search_dir):
        if any(ignored in root for ignored in [".venv", "node_modules", ".git", ".system_generated", "__pycache__"]):
            continue
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in supported_exts:
                fpath = os.path.join(root, file)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                    # Chunk into 40-line blocks
                    for i in range(0, len(lines), 30):
                        block = "".join(lines[i:i+40]).strip()
                        if len(block) > 40:
                            chunks.append({
                                "file": fpath,
                                "start_line": i + 1,
                                "end_line": min(len(lines), i + 40),
                                "content": block
                            })
                except Exception:
                    pass

    if not chunks:
        return []

    # Limit to top 25 chunks for embedding
    candidate_chunks = chunks[:25]
    texts = [c["content"][:600] for c in candidate_chunks]
    doc_embeds = generate_cloudflare_embeddings(texts)

    if not doc_embeds or len(doc_embeds) != len(candidate_chunks):
        return []

    # Compute Cosine Similarities in pure Python
    def dot_product(v1, v2):
        return sum(x * y for x, y in zip(v1, v2))

    def magnitude(v):
        return sum(x * x for x in v) ** 0.5

    scored = []
    q_mag = magnitude(q_vec)
    for chunk, d_vec in zip(candidate_chunks, doc_embeds):
        d_mag = magnitude(d_vec)
        if q_mag > 0 and d_mag > 0:
            score = dot_product(q_vec, d_vec) / (q_mag * d_mag)
            scored.append({"score": round(score, 4), **chunk})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:5]


# =========================================================================
# 5. CLOUDFLARE WORKERS AI DEEPSEEK-R1 (REASONING & DEBUGGING)
# =========================================================================
def call_cloudflare_reasoning(messages: list, max_tokens: int = 4096) -> dict:
    """
    Invokes DeepSeek-R1 Distill on Cloudflare Workers AI for deep reasoning & self-healing.
    """
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"
    t0 = time.time()
    try:
        r = requests.post(url, headers=_get_headers(True), json={"messages": messages, "max_tokens": max_tokens}, timeout=50)
        dt = time.time() - t0
        if r.status_code == 200:
            res = r.json().get("result", {})
            content = res.get("response", "")
            return {
                "ok": True,
                "content": content,
                "duration": dt,
                "model": "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
                "provider": "cloudflare_r1"
            }
        return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:150]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
