from langchain_huggingface import HuggingFaceEmbeddings
print("Imported HuggingFaceEmbeddings")
try:
    embeddings = HuggingFaceEmbeddings(model_name="thenlper/gte-small")
    print("Initialized HuggingFaceEmbeddings")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
