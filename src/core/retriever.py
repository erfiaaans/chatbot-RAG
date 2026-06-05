import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.services.embedding_service import EmbeddingService
from src.services.vector_store import VectorStore
from src.config.config import settings
class QueryEmbedder:
    def __init__(self):
        self.embedder = EmbeddingService()
    def embed_query(self, question: str) -> list[float]:
        question = question.strip().lower()
        return self.embedder.embed_query(question)
class Retriever:
    def __init__(self):
        self.store = VectorStore()
        self.embedder = QueryEmbedder()
    def retrieve(self, question: str) -> list[dict]:
        vector = self.embedder.embed_query(question)
        results = self.store.search(vector, k=settings.top_k)
        docs = results.get("documents") or []
        metas = results.get("metadatas") or []
        dists = results.get("distances") or []
        if not docs:
            return []
        return [
            {"text": d, "meta": m, "distance": dist}
            for d, m, dist in zip(docs[0], metas[0], dists[0])
        ]
#Testing
if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table
    from rich import box

    console = Console()

    # ── Query Embedder ──────────────────────────────────────
    print("\nPengujian Query Embedder")
    print("=" * 50)

    embedder = QueryEmbedder()
    sample_query = "Apa syarat pengajuan judul skripsi?"
    vector = embedder.embed_query(sample_query)

    table_embed = Table(
        title="Query Embedder Result",
        box=box.ROUNDED,
        show_lines=True,
        header_style="bold black"
    )
    table_embed.add_column("Query Input",    style="black", width=40)
    table_embed.add_column("Dimensi Vektor", style="black", width=15, justify="center")
    table_embed.add_column("Sampel Vektor",  style="black", width=40)

    table_embed.add_row(
        sample_query,
        str(len(vector)),
        str([round(v, 4) for v in vector[:5]]) + " ...",
    )

    console.print(table_embed)
    print("[OK] Query Embedder berhasil menghasilkan vektor.")

    # ── Retriever ───────────────────────────────────────────
    print("\nPengujian Retriever")
    print("=" * 50)

    retriever = Retriever()
    test_queries = [
        "Apa saja isi dari Kajian Teoritis?",
        "Bagaimana format penulisan daftar pustaka?",
    ]

    for i, query in enumerate(test_queries, 1):
        results = retriever.retrieve(query)

        table_ret = Table(
            title=f"Query {i}: {query}",
            box=box.ROUNDED,
            show_lines=True,
            header_style="bold black"
        )
        table_ret.add_column("No",       style="black", width=4,  justify="center")
        table_ret.add_column("Header",   style="black", width=30)
        table_ret.add_column("Distance", style="black", width=10, justify="center")
        table_ret.add_column("Preview",  style="black", width=55)

        if not results:
            table_ret.add_row("-", "Tidak ada dokumen ditemukan.", "-", "-")
        else:
            for j, res in enumerate(results, 1):
                table_ret.add_row(
                    str(j),
                    res["meta"].get("header", "-"),
                    f"{res['distance']:.4f}",
                    res["text"][:120].replace("\n", " ") + "...",
                )

        console.print(table_ret)

    print("=" * 50)
    print("Pengujian Modul Retrieval selesai.")
    print("=" * 50)
# if __name__ == "__main__":
#     print("\nPengujian Query Embedder")
#     print("=" * 40)

#     embedder = QueryEmbedder()

#     sample_query = "Apa syarat pengajuan judul skripsi?"
#     vector = embedder.embed_query(sample_query)

#     print(f"Query Input   : {sample_query}")
#     print(f"Dimensi Vektor: {len(vector)}")
#     print(f"Sampel Vektor : {vector[:5]} ...")
#     print("[OK] Query Embedder berhasil menghasilkan vektor.")

#     print("\nPengujian Retriever")
#     print("=" * 40)

#     retriever = Retriever()

#     test_queries = [
#         "Apa saja isi dari Kajian Teoritis?",
#         "Bagaimana format penulisan daftar pustaka?",
#     ]

#     for i, query in enumerate(test_queries, 1):
#         print(f"\nQuery {i}: {query}")
#         results = retriever.retrieve(query)

#         if not results:
#             print("  [!] Tidak ada dokumen ditemukan.")
#             continue

#         print(f"  Jumlah hasil : {len(results)} dokumen")
#         for j, res in enumerate(results, 1):
#             header   = res["meta"].get("header", "-")
#             distance = res["distance"]
#             preview  = res["text"][:120].replace("\n", " ")
#             print(f"\n  [Hasil {j}]")
#             print(f"    Header   : {header}")
#             print(f"    Distance : {distance:.4f}")
#             print(f"    Preview  : {preview}...")

#     print("\n" + "=" * 60)
#     print("Pengujian Modul Retrieval selesai.")
#     print("=" * 60)