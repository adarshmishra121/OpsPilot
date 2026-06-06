import json
import os

import faiss
import numpy as np

# Create dummy anomaly vocab
os.makedirs("artifacts", exist_ok=True)
with open("artifacts/anomaly_vocab.json", "w") as f:
    json.dump({"version": 1, "words": {}}, f)
with open("artifacts/anomaly_model.pkl", "w") as f:
    f.write("dummy")

# Create dummy FAISS index so we don't zero-divide on empty empty embeddings
os.makedirs("models/faiss_index", exist_ok=True)
d = 384  # all-MiniLM-L6-v2 dimension
index = faiss.IndexFlatIP(d)
# add 1 dummy vector
vecs = np.random.random((1, d)).astype("float32")
index.add(vecs)
faiss.write_index(index, "models/faiss_index/index.faiss")

# Create dummy metadata
with open("models/faiss_index/meta.jsonl", "w") as f:
    f.write(json.dumps({"text": "dummy error log", "source": "test"}) + "\n")

print("Created dummy artifacts/models for testing.")
