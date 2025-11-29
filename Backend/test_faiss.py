from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import faiss
import pickle
from langchain_community.docstore.in_memory import InMemoryDocstore

print("Imports successful")

try:
    embedding_model = HuggingFaceEmbeddings(model_name="thenlper/gte-small")
    
    index = faiss.IndexFlatL2(384)
    docstore = InMemoryDocstore({})
    index_to_docstore_id = {}
    
    vector_db = FAISS(
        index=index,
        docstore=docstore,
        index_to_docstore_id=index_to_docstore_id,
        embedding_function=embedding_model
    )
    print("FAISS initialized")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
