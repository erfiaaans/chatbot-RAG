import re
from typing import List

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from config import settings


class TextChunker:
    def __init__(self):
        self.splitter = SentenceSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separator="\n\n",
        )

    # ==============================
    # MAIN FUNCTION
    # ==============================
    def chunk(self, text: str, metadata: dict) -> List[Document]:
        docs = []

        header_split = re.split(r"(#+ .+)", text)

        sections = []
        header_stack = []  # FIX: pakai list (bukan dict)

        for part in header_split:
            part = part.strip()

            if not part:
                continue

            # ==============================
            # DETECT HEADER
            # ==============================
            if re.match(r"#+ ", part):
                level = len(part) - len(part.lstrip("#"))
                header_text = part.strip("# ").strip()

                # adjust hierarchy stack
                header_stack = header_stack[: level - 1]
                header_stack.append(header_text)

            else:
                if part.strip():
                    # ==============================
                    # BUILD BREADCRUMB STRING
                    # ==============================
                    full_header = " > ".join(header_stack).strip()

                    sections.append((full_header, part.strip()))

        chunk_id = 0

        # ==============================
        # CHUNKING
        # ==============================
        for header, body in sections:
            # normalize newline (stabil untuk embedding)
            body = re.sub(r"(?<!\n)\n(?!\n)", " ", body)

            sub_chunks = self.splitter.split_text(body)

            for sc in sub_chunks:
                # ==============================
                # COMBINE HEADER + CONTENT
                # ==============================
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

                # ==============================
                # DEBUG LOG
                # ==============================
                # print("\n" + "-" * 80)
                # print(f"Chunk ID : {chunk_id}")
                # print(f"Doc ID   : {doc_id}")
                # print(f"Header   : {header if header else '-'}")
                # print(f"Length   : {len(sc)} chars")
                # print("-" * 80)
                # print(text_with_header)
                # print("-" * 80)

                chunk_id += 1

        return docs
