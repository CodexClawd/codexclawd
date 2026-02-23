#!/usr/bin/env python3
"""
Vector Memory Pipeline
- Maintains a FAISS index of memory chunks
- Uses sentence-transformers (all-MiniLM-L6-v2, 384-dim)
- Provides semantic search over past conversations
"""

import json
import pickle
from datetime import datetime
from pathlib import Path
import hashlib

# Lazy imports to avoid requirement if not used
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    import faiss
    HAVE_DEPS = True
except ImportError:
    HAVE_DEPS = False

WORKSPACE = Path("/home/boss/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
VECTOR_DIR = MEMORY_DIR / "vector"
INDEX_FILE = VECTOR_DIR / "index.faiss"
META_FILE = VECTOR_DIR / "metadata.pkl"
CHUNK_FILE = VECTOR_DIR / "chunks.jsonl"

VECTOR_DIR.mkdir(parents=True, exist_ok=True)

class VectorMemory:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        if not HAVE_DEPS:
            raise RuntimeError("sentence-transformers and faiss-cpu not installed")
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.chunks = []  # list of dicts: {"text": ..., "source": ..., "ts": ...}
        self.load()

    def load(self):
        if INDEX_FILE.exists() and META_FILE.exists():
            self.index = faiss.read_index(str(INDEX_FILE))
            with open(META_FILE, "rb") as f:
                data = pickle.load(f)
            self.chunks = data["chunks"]
        else:
            self.index = faiss.IndexFlatL2(self.dim)
            self.chunks = []

    def save(self):
        faiss.write_index(self.index, str(INDEX_FILE))
        with open(META_FILE, "wb") as f:
            pickle.dump({"chunks": self.chunks}, f)

    def add_chunk(self, text, source="unknown", ts=None):
        if ts is None:
            ts = datetime.utcnow().isoformat()
        embedding = self.model.encode(text)
        self.index.add(np.array([embedding], dtype=np.float32))
        self.chunks.append({"text": text, "source": source, "ts": ts})
        self.save()

    def rebuild_from_memory(self):
        """Scan memory/*.md and hourly/*.md to rebuild index"""
        self.index = faiss.IndexFlatL2(self.dim)
        self.chunks = []
        count = 0
        for md_file in list((MEMORY_DIR).glob("*.md")) + list((MEMORY_DIR / "hourly").glob("*.md")):
            try:
                content = md_file.read_text(encoding="utf-8")
                # Split into paragraphs of at least 50 chars
                paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 50]
                for para in paragraphs[:10]:  # limit per file to prevent huge index
                    self.add_chunk(para, source=str(md_file.name), ts=md_file.stat().st_mtime)
                    count += 1
            except:
                continue
        print(f"Rebuilt vector index: {count} chunks")

    def search(self, query, k=10):
        if self.index.ntotal == 0:
            return []
        q_emb = self.model.encode(query)
        D, I = self.index.search(np.array([q_emb], dtype=np.float32), k)
        results = []
        for dist, idx in zip(D[0], I[0]):
            if 0 <= idx < len(self.chunks):
                results.append({
                    "text": self.chunks[idx]["text"],
                    "source": self.chunks[idx]["source"],
                    "ts": self.chunks[idx]["ts"],
                    "distance": float(dist)
                })
        return results

def main():
    if len(sys.argv) < 2:
        print("Usage: vector-memory.py rebuild | search <query>")
        sys.exit(1)

    vm = VectorMemory()
    cmd = sys.argv[1]

    if cmd == "rebuild":
        vm.rebuild_from_memory()
        print(f"Index now has {vm.index.ntotal} vectors")
    elif cmd == "search":
        query = " ".join(sys.argv[2:])
        results = vm.search(query, k=5)
        for i, r in enumerate(results, 1):
            print(f"{i}. [{r['source']}] score={1-r['distance']:.3f}")
            print(f"   {r['text'][:300]}...\n")
    else:
        print("Unknown command")

if __name__ == "__main__":
    main()
