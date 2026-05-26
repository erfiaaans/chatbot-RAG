import re
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
