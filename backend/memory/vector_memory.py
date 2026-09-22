import json
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer


class VectorMemory:

    def __init__(self):

        # Project root
        self.base_dir = Path(__file__).resolve().parents[2]

        # Storage paths
        self.data_dir = self.base_dir / "data"

        self.data_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.index_file = (
            self.data_dir / "memory.index"
        )

        self.memory_file = (
            self.data_dir / "vector_memories.json"
        )

        # Embedding model
        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        # Embedding dimension
        self.dimension = 384

        # Load existing index
        if self.index_file.exists():

            self.index = faiss.read_index(
                str(self.index_file)
            )

        else:

            self.index = faiss.IndexFlatL2(
                self.dimension
            )

        # Load stored memories
        if self.memory_file.exists():

            try:

                with open(
                    self.memory_file,
                    "r",
                    encoding="utf-8"
                ) as file:

                    self.memories = json.load(file)

            except json.JSONDecodeError:

                self.memories = []

        else:

            self.memories = []

    # ========================================================
    # SAVE MEMORY
    # ========================================================

    def save(self, question, answer):

        text = (
            f"Question: {question}\n"
            f"Answer: {answer}"
        )

        # Create embedding
        embedding = self.model.encode(
            [text]
        )

        # Convert to float32
        embedding = embedding.astype("float32")

        # Add to FAISS
        self.index.add(embedding)

        # Save memory information
        self.memories.append({
            "question": question,
            "answer": answer
        })

        self._save()

    # ========================================================
    # SEARCH MEMORY
    # ========================================================

    def search(self, query, limit=5):

        if not self.memories:

            return []

        # Convert query to embedding
        query_embedding = self.model.encode(
            [query]
        )

        query_embedding = query_embedding.astype(
            "float32"
        )

        # Number of results
        k = min(
            limit,
            len(self.memories)
        )

        # Search FAISS
        distances, indices = self.index.search(
            query_embedding,
            k
        )

        results = []

        for index in indices[0]:

            if index == -1:
                continue

            if index < len(self.memories):

                results.append(
                    self.memories[index]
                )

        return results

    # ========================================================
    # SAVE TO DISK
    # ========================================================

    def _save(self):

        # Save FAISS index
        faiss.write_index(
            self.index,
            str(self.index_file)
        )

        # Save memory metadata
        with open(
            self.memory_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.memories,
                file,
                indent=4,
                ensure_ascii=False
            )

    # ========================================================
    # CLEAR MEMORY
    # ========================================================

    def clear(self):

        self.index = faiss.IndexFlatL2(
            self.dimension
        )

        self.memories = []

        self._save()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("          AGENTFORGE - VECTOR MEMORY")
    print("=" * 60)

    memory = VectorMemory()

    print("\nSaving test memories...")

    memory.save(
        "What is artificial intelligence?",
        "AI is the field of creating machines that "
        "can perform tasks requiring intelligence."
    )

    memory.save(
        "What is Python?",
        "Python is a popular programming language."
    )

    print("Memories saved.")

    print("\nSearching for:")
    print("How does AI work?")

    results = memory.search(
        "How does AI work?",
        limit=3
    )

    print("\nRelevant memories:\n")

    for item in results:

        print(
            "Question:",
            item["question"]
        )

        print(
            "Answer:",
            item["answer"]
        )

        print("-" * 50)