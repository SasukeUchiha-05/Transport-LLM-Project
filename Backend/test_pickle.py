import pickle
import sys

try:
    with open("models/faiss_metadata_LOL.pkl", "rb") as f:
        metadata = pickle.load(f)
    print("Pickle loaded successfully")
    print(f"Keys: {metadata.keys()}")
    if 'docstore' in metadata:
        print(f"Docstore type: {type(metadata['docstore'])}")
        # Try to inspect one document
        # metadata['docstore'] is likely a dict or an object
        ds = metadata['docstore']
        print(f"Docstore content type: {type(ds)}")
        
except Exception as e:
    print(f"Error loading pickle: {e}")
    import traceback
    traceback.print_exc()
