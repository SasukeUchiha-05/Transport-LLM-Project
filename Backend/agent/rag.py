"""
agent/rag.py
Refactored to:
 - use google-genai directly (no langchain Google wrapper)
 - optionally run DuckDuckGo web searches when the user asks for links/sources
 - instruct GenAI to include markdown links when a link request is detected

Requires:
 - google-genai (pip install google-genai)
 - duckduckgo_search (optional; pip install duckduckgo_search)
Set env var: GOOGLE_API_KEY
"""

import os
import pickle
from typing import Optional, List, Dict, Tuple
from dotenv import load_dotenv
load_dotenv()

# FAISS + embeddings + docstore (kept from prior flow)
import faiss
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_core.documents import Document

# Google GenAI client (modern SDK)
# If your environment uses "from google import genai" style, keep it; otherwise adjust as needed.
try:
    from google import genai  # google-genai package
except Exception as e:
    genai = None
    print(f"[import] google.genai import failed: {e}. Make sure google-genai is installed.")

# DuckDuckGo search (optional). We'll import lazily in search_web to avoid hard dependency.
# from duckduckgo_search import ddg (used lazily)

# Globals
KNOWLEDGE_VECTOR_DATABASE: Optional[FAISS] = None
genai_client: Optional[object] = None
EMBEDDING_MODEL = None


# -------------------------
# Initialization
# -------------------------
def init_agent(embed_device: str = "cpu"):
    """
    Initialize:
      - HuggingFace embeddings (thenlper/gte-small by default)
      - Load FAISS index + metadata into a FAISS vectorstore wrapper
      - Initialize Google GenAI client (genai.Client) if google-genai is available
    """
    global KNOWLEDGE_VECTOR_DATABASE, genai_client, EMBEDDING_MODEL

    print("Initializing Agent...")

    # Embeddings
    try:
        EMBEDDING_MODEL = HuggingFaceEmbeddings(
            model_name="thenlper/gte-small",
            multi_process=True,
            model_kwargs={"device": embed_device},
            encode_kwargs={"normalize_embeddings": True},
        )
        print("[embeddings] HuggingFace embeddings initialized")
    except Exception as e:
        print(f"[embeddings] Failed to init embeddings: {e}")
        EMBEDDING_MODEL = None

    # FAISS index + docstore load
    index_path = "models/faiss_index_LOL.bin"
    metadata_path = "models/faiss_metadata_LOL.pkl"
    if os.path.exists(index_path) and os.path.exists(metadata_path) and EMBEDDING_MODEL is not None:
        try:
            index = faiss.read_index(index_path)
            with open(metadata_path, "rb") as f:
                metadata = pickle.load(f)

            old_docstore = metadata.get("docstore", {}) if isinstance(metadata, dict) else {}
            new_docstore = {}
            for k, v in old_docstore.items():
                try:
                    if isinstance(v, Document):
                        new_doc = Document(page_content=v.page_content, metadata=v.metadata)
                    elif isinstance(v, dict):
                        new_doc = Document(page_content=v.get("page_content", ""), metadata=v.get("metadata", {}))
                    else:
                        new_doc = Document(page_content=str(v), metadata={})
                    new_docstore[k] = new_doc
                except Exception as e:
                    print(f"[docstore] Skipping item {k}: {e}")

            docstore = InMemoryDocstore(new_docstore)
            index_to_docstore_id = metadata.get("index_to_docstore_id", None)
            KNOWLEDGE_VECTOR_DATABASE = FAISS(
                index=index,
                docstore=docstore,
                index_to_docstore_id=index_to_docstore_id,
                embedding_function=EMBEDDING_MODEL,
            )
            print("[faiss] Vector database initialized.")
        except Exception as e:
            print(f"[faiss] Error loading FAISS: {e}")
            KNOWLEDGE_VECTOR_DATABASE = None
    else:
        print(f"[faiss] Index/metadata not found at {index_path}/{metadata_path} or embedding not initialized.")

    # GenAI client init
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("[genai] GOOGLE_API_KEY not set. GenAI client will not be initialized.")
        genai_client = None
        return

    if genai is None:
        print("[genai] google-genai client not available (import failed). Install google-genai.")
        genai_client = None
        return

    try:
        genai_client = genai.Client(api_key=google_api_key)
        print("[genai] GenAI client initialized.")
    except Exception as e:
        print(f"[genai] Failed to init GenAI client: {e}")
        genai_client = None


# -------------------------
# Web search utilities (DuckDuckGo)
# -------------------------
def is_link_request(question: str) -> bool:
    """
    Basic heuristic: detect if the user asked for links/sources/references.
    You can expand this to a more robust classifier or regex.
    """
    q = question.lower()
    keywords = ["link", "links", "source", "sources", "reference", "references", "where can i find", "website", "web results", "url"]
    return any(k in q for k in keywords)


def search_web_duckduckgo(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Use duckduckgo_search.DDGS to fetch search results.
    Returns list of dicts: {title, href, body}
    If package not installed or search fails, returns empty list.
    """
    try:
        from duckduckgo_search import DDGS
    except Exception as e:
        print(f"[websearch] duckduckgo_search not installed or failed to import: {e}")
        return []

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            
        out = []
        if not results:
            return out
        for r in results:
            out.append({
                "title": r.get("title", "")[:180],
                "href": r.get("href", ""),
                "snippet": r.get("body", "")[:400]
            })
        return out
    except Exception as e:
        print(f"[websearch] DuckDuckGo query failed: {e}")
        return []


# -------------------------
# RAG retrieval
# -------------------------
def retrieve_context(query: str, k: int = 3, score_threshold: float = 0.70) -> str:
    """
    Do a similarity search on FAISS and return concatenated context.
    """
    global KNOWLEDGE_VECTOR_DATABASE
    if not KNOWLEDGE_VECTOR_DATABASE:
        print("[retrieve_context] No vector DB initialized.")
        return ""

    try:
        retrieved = KNOWLEDGE_VECTOR_DATABASE.similarity_search_with_relevance_scores(query, k=k)
    except Exception as e:
        print(f"[retrieve_context] Retrieval error: {e}")
        return ""

    if not retrieved:
        print("[retrieve_context] No docs retrieved.")
        return ""

    context_parts = []
    for item in retrieved:
        try:
            if isinstance(item, (list, tuple)):
                doc, score = item[0], item[1]
            else:
                doc, score = item, None

            # NOTE: check whether score is similarity (higher better) or distance (lower better) in your setup.
            if score is not None and (score < score_threshold):
                continue

            context_parts.append(doc.page_content)
        except Exception as e:
            print(f"[retrieve_context] Error processing retrieved item: {e}")

    return "\n\n".join(context_parts)


# -------------------------
# GenAI response parsing
# -------------------------
def _extract_text_from_genai_response(resp) -> str:
    """
    Robustly extract text from various genai response shapes.
    """
    if resp is None:
        return ""

    try:
        if hasattr(resp, "text") and resp.text:
            return resp.text
    except Exception:
        pass

    try:
        if hasattr(resp, "result"):
            r = resp.result
            if isinstance(r, (list, tuple)) and len(r) > 0:
                first = r[0]
                # common patterns
                for attr in ("output", "content", "candidates"):
                    if hasattr(first, attr):
                        candidate = getattr(first, attr)
                        if isinstance(candidate, (list, tuple)) and len(candidate) > 0:
                            c0 = candidate[0]
                            for f in ("text", "content"):
                                if hasattr(c0, f):
                                    return getattr(c0, f)
                return str(first)
    except Exception:
        pass

    try:
        return str(resp)
    except Exception:
        return ""


# -------------------------
# Prompt building & generation
# -------------------------
def _build_prompt(question: str, context: Optional[str], web_results: Optional[List[Dict[str, str]]], require_links: bool) -> str:
    """
    Build a clear prompt for the model that:
     - instructs it to use context (if available)
     - includes web search results (if any)
     - instructs it to include markdown links when require_links True
    """
    system_instruction = (
        "You are a concise, helpful transport assistant. Use ONLY the facts from the provided context and web search results "
        "to answer the user's question. Greet the user briefly, then give a direct, concise answer. If asked for links or sources, "
        "return relevant results as clickable markdown links (e.g., [title](url)). Do not hallucinate links. If context or web results "
        "do not contain enough information, say you don't know and suggest how to find it."
    )

    parts = [system_instruction, ""]

    if context:
        parts.append("CONTEXT:\n" + context + "\n")
    if web_results:
        parts.append("WebSearchResults:\n")
        for i, r in enumerate(web_results, start=1):
            # include simple numbered list that the model can reference
            parts.append(f"{i}. {r.get('title','')}\n   URL: {r.get('href','')}\n   Snippet: {r.get('snippet','')}\n")
        parts.append("")

    # user question and formatting instructions
    parts.append("---")
    parts.append("User Question:\n" + question + "\n")
    if require_links:
        parts.append(
            "Important: The user asked for links/sources. Provide a concise answer AND list the most relevant links as markdown bullets under a section titled 'Sources'. "
            "Example:\nAnswer: <one paragraph>\n\nSources:\n- [Title 1](https://...)\n- [Title 2](https://...)\n\nOnly include links that appear in the WebSearchResults above; do NOT invent URLs."
        )
    else:
        parts.append("Important: Do not provide external links unless the user explicitly asked for them.")
    return "\n".join(parts)


def generate_response(question: str, context: Optional[str]) -> Tuple[str, List[Dict[str, str]]]:
    """
    Generate an answer using GenAI. If user asked for links, perform a DuckDuckGo search and include results.
    Returns: (answer_text, web_results_used)
    """
    global genai_client
    if genai_client is None:
        return ("Error: GenAI client not initialized. Set GOOGLE_API_KEY and call init_agent().", [])

    # Detect if the user asked for links/sources
    require_links = is_link_request(question)

    web_results = []
    if require_links:
        # run a web search, include top 5 results
        web_results = search_web_duckduckgo(question, max_results=5)
        if not web_results:
            # if duckduckgo_search not installed or failed, warn the model (so GenAI won't hallucinate)
            web_results = []

    # If we have RAG context, include that too. If both web results & context present, model should use both.
    prompt = _build_prompt(question, context, web_results if web_results else None, require_links)

    # call the model
    try:
        resp = genai_client.models.generate_content(model="gemini-2.5-pro", contents=prompt)
    except Exception as e:
        # fallback older style or different sdk entrypoints
        try:
            # some SDK variants expose top-level generate
            resp = genai.generate(model="models/gemini-2.5-pro", messages=[{"role": "user", "content": prompt}])
        except Exception as e2:
            return (f"[genai] Error calling model.generate_content: {e}; fallback error: {e2}", web_results)

    out_text = _extract_text_from_genai_response(resp)

    # If require_links is True, the model's output should include a 'Sources' section with markdown links.
    return (out_text, web_results)


# -------------------------
# Quick manual test
# -------------------------
if __name__ == "__main__":
    init_agent()
    # Example 1: normal RAG question
    ctx = retrieve_context("What is the ticket booking workflow?")
    print("CONTEXT (truncated):", (ctx or "")[:400], "...\n")
    ans, web = generate_response("How to book a ticket?", ctx)
    print("Answer:\n", ans)
    if web:
        print("\nWeb results returned (not necessarily shown in answer):")
        for r in web:
            print("-", r.get("title"), r.get("href"))

    # Example 2: user explicitly asks for links
    q2 = "Where can I find documentation or guides about ticket booking integrations? Please provide links."
    ctx2 = retrieve_context(q2)
    ans2, web2 = generate_response(q2, ctx2)
    print("\nQ2 Answer:\n", ans2)
    if web2:
        print("\nWeb results used:")
        for r in web2:
            print("-", r.get("title"), r.get("href"))
