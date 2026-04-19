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
        header_stack = {}

        for part in header_split:
            if re.match(r"#+ ", part):
                level = part.count("#")
                header_text = part.strip("# ").strip()
                header_stack[level] = header_text

                # hapus header level bawah
                for l in list(header_stack.keys()):
                    if l > level:
                        del header_stack[l]

            else:
                if part.strip():
                    level1 = header_stack.get(1, "")
                    level2 = header_stack.get(2, "")
                    level3 = header_stack.get(3, "")
                    level4 = header_stack.get(4, "")

                    full_header = " ".join(
                        h for h in [level1, level2, level3, level4] if h
                    )

                    sections.append((full_header, part.strip()))

        chunk_id = 0

        for header, body in sections:
            paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]

            for para in paragraphs:
                sub_chunks = self.splitter.split_text(para)

                for sc in sub_chunks:
                    text_with_header = f"{header}\n\n{sc}" if header else sc

                    docs.append(
                        Document(
                            id_=f"{metadata['filename']}_chunk_{chunk_id}",
                            text=text_with_header,
                            metadata={
                                "source": metadata.get("filename"),
                                "category": metadata.get("category"),
                                "path": metadata.get("path"),
                                "header": header,
                            },
                        )
                    )

                    chunk_id += 1

        return docs
