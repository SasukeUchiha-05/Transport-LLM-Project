"""
agent/rag.py
Refactored to use google-genai directly (no langchain Google wrapper).
Requires: google-genai (pip install google-genai)
Set env var: GOOGLE_API_KEY
"""

import os
import pickle
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

# faiss + embeddings + docstore
import faiss
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_core.documents import Document

# Google GenAI client (modern SDK)
from google import genai

# Globals
KNOWLEDGE_VECTOR_DATABASE: Optional[FAISS] = None
genai_client: Optional[genai.Client] = None
EMBEDDING_MODEL = None


def init_agent(embed_device: str = "cpu"):
    """
    Initialize:
      - HuggingFace embeddings (thenlper/gte-small by default)
      - Load FAISS index + metadata into a FAISS vectorstore wrapper
      - Initialize Google GenAI client (genai.Client)
    """
    global KNOWLEDGE_VECTOR_DATABASE, genai_client, EMBEDDING_MODEL

    print("Initializing Agent...")

    # -------------------------
    # Embeddings
    # -------------------------
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

    # -------------------------
    # FAISS index + docstore load
    # -------------------------
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

    # -------------------------
    # GenAI client init
    # -------------------------
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("[genai] GOOGLE_API_KEY not set. GenAI client will not be initialized.")
        genai_client = None
        return

    try:
        # Initialize client. You can pass api_key or rely on env.
        genai_client = genai.Client(api_key=google_api_key)
        print("[genai] GenAI client initialized.")
    except Exception as e:
        print(f"[genai] Failed to init GenAI client: {e}")
        genai_client = None


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
            # handle (Document, score) vs Document only
            if isinstance(item, (list, tuple)):
                doc, score = item[0], item[1]
            else:
                doc, score = item, None

            # If scores are distances or similarities, you may need to invert/adjust threshold logic.
            if score is not None and (score < score_threshold):
                # skip low-score (assumes higher is better). Adjust if your scores are distances.
                continue

            context_parts.append(doc.page_content)
        except Exception as e:
            print(f"[retrieve_context] Error processing retrieved item: {e}")

    # join with newlines; consider truncation later
    return "\n\n".join(context_parts)


def _extract_text_from_genai_response(resp) -> str:
    """
    Robustly extract text from various genai response shapes.
    The google-genai responses often expose .text, or .result / .candidates, etc.
    """
    if resp is None:
        return ""

    # prefer .text if present
    try:
        if hasattr(resp, "text") and resp.text:
            return resp.text
    except Exception:
        pass

    # newer client samples show resp.result[0].content[0].text
    try:
        # resp.result may be a sequence of output objects
        if hasattr(resp, "result"):
            # some SDK responses are typed; try common nesting patterns
            r = resp.result
            if isinstance(r, (list, tuple)) and len(r) > 0:
                # try to find text inside first result
                first = r[0]
                # some wrappers: first.output[0].content[0].text or first.content[0].text
                for attr in ("output", "content", "candidates"):
                    if hasattr(first, attr):
                        candidate = getattr(first, attr)
                        if isinstance(candidate, (list, tuple)) and len(candidate) > 0:
                            c0 = candidate[0]
                            # common field names:
                            for f in ("text", "content"):
                                if hasattr(c0, f):
                                    return getattr(c0, f)
                # fallback to string
                return str(first)
    except Exception:
        pass

    # fallback to stringifying whole response
    try:
        return str(resp)
    except Exception:
        return ""


def generate_response(question: str, context: Optional[str], model: str = "gemini-2.5-pro"):
    """
    Build a prompt using the context and question and call GenAI directly.
    Returns the model's text output (string).
    """
    global genai_client
    if genai_client is None:
        return "Error: GenAI client not initialized. Set GOOGLE_API_KEY and call init_agent()."

    # System instruction + context + user question in a single prompt
    system_prompt = (
        "You are a concise, helpful transport-assistant. Use only facts from the provided context when answering. "
        "Greet the user briefly and then answer the question. Be concise and relevant."
    )

    if context:
        prompt = (
            f"{system_prompt}\n\n"
            f"Context:\n{context}\n\n"
            f"---\nQuestion: {question}\n\n"
            "Answer concisely using only the context above."
        )
    else:
        prompt = (
            "You are a transport-focused assistant. You cannot answer this question because the knowledge base is empty "
            "or no relevant context was found. Politely inform the user you cannot answer and ask them to ask questions "
            "related to transport services only.\n\n"
            f"Question: {question}"
        )

    try:
        # The modern google-genai SDK exposes client.models.generate_content
        resp = genai_client.models.generate_content(model=model, contents=prompt)
    except Exception as e:
        # Try older style generate if available
        try:
            resp = genai.generate(model=model, messages=[{"role": "user", "content": prompt}])
        except Exception as e2:
            return f"[genai] Error calling model.generate_content: {e}; fallback error: {e2}"

    # extract text robustly
    out_text = _extract_text_from_genai_response(resp)
    return out_text


if __name__ == "__main__":
    # quick manual test
    init_agent()
    ctx = retrieve_context("What is the ticket booking workflow?")
    print("CONTEXT:", ctx[:400], "...")
    print("LLM answer:", generate_response("How to book a ticket?", ctx))
