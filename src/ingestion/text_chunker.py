import re
import os
import sys

from annotated_types import doc
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from typing import List
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from src.config.config import settings
class TextChunker:
    def __init__(self):
        self.splitter = SentenceSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separator="\n\n",
        )
    def chunk(self, text: str, metadata: dict) -> List[Document]:
        docs = []
        header_split = re.split(r"(#+ .+)", text)
        sections = []
        header_stack = [] 
        for part in header_split:
            part = part.strip()
            if not part:
                continue
            if re.match(r"#+ ", part):
                level = len(part) - len(part.lstrip("#"))
                header_text = part.strip("# ").strip()
                header_stack = header_stack[: level - 1]
                header_stack.append(header_text)
            else:
                if part.strip():
                    full_header = " > ".join(header_stack).strip()
                    sections.append((full_header, part.strip()))
        chunk_id = 0
        for header, body in sections:
            body = re.sub(r"(?<!\n)\n(?!\n)", " ", body)
            sub_chunks = self.splitter.split_text(body)
            for sc in sub_chunks:
                text_with_header = f"{header}\n\n{sc}" if header else sc
                doc_id = f"{metadata['filename']}_chunk_{chunk_id}"
                doc = Document(
                    id_=doc_id,
                    text=text_with_header,
                    metadata={
                        "source": metadata.get("filename"),
                        "category": metadata.get("category"),
                        "path": metadata.get("path"),
                        "header": header,
                        "key_id": doc_id,
                    },
                )
                docs.append(doc)
                chunk_id += 1
        return docs

# Testing
if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from src.ingestion.document_loader import DocumentLoader

    loader = DocumentLoader()
    documents = loader.load_folder("data/")

    chunker = TextChunker()
    all_chunks = []
    for doc in documents:
        chunks = chunker.chunk(doc["text"], doc)
        all_chunks.extend(chunks)

    console = Console()

    print("=" * 50)
    print(f"Total Dokumen : {len(documents)}")
    print(f"Total Chunk   : {len(all_chunks)}")
    print("=" * 50)

    table = Table(
        title="Preview 5 Chunk Pertama",
        box=box.ROUNDED,
        show_lines=True,
        header_style="bold black"
    )
    table.add_column("Chunk",    style="black", width=6,  justify="center")
    table.add_column("Category", style="black", width=20)
    table.add_column("ID",       style="black", width=30)
    table.add_column("Header",   style="black", width=22)
    table.add_column("Preview",  style="black", width=45)

    for i, chunk in enumerate(all_chunks[:5]):
        table.add_row(
            str(i),
            chunk.metadata["category"] or "-",
            chunk.id_,
            chunk.metadata["header"] or "-",
            chunk.text[:100].replace("\n", " ") + "...",
        )

    console.print(table)
    print(f"TextChunker berhasil! {len(all_chunks)} chunk dari {len(documents)} dokumen.")
# if __name__ == "__main__":
#     import sys
#     sys.path.append("src")

#     from src.ingestion.document_loader import DocumentLoader

#     # Load file asli
#     loader = DocumentLoader()
#     doc = loader.load("data/Skripsi/KB_PEDOMAN_SKRIPSI_BAB II.md")

#     # Chunk hasilnya
#     chunker = TextChunker()
#     chunks = chunker.chunk(doc["text"], doc)

#     print("=" * 50)
#     print(f"Filename   : {doc['filename']}")
#     print(f"Category   : {doc['category']}")
#     print(f"Total chunk: {len(chunks)}")
#     print("=" * 50)
#     for i, chunk in enumerate(chunks[:3]):  # preview 3 chunk pertama
#         print(f"\n[Chunk {i}]")
#         print(f"  ID      : {chunk.id_}")
#         print(f"  Header  : {chunk.metadata['header']}")
#         print(f"  Preview : {chunk.text[:150]}")
#     print("\n" + "=" * 50)
#     print("TextChunker berhasil!")
