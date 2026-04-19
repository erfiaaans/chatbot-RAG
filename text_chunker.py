import re
from typing import List

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter

from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNK_SIZE, CHUNK_OVERLAP

class TextChunker:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size        = CHUNK_SIZE,
            chunk_overlap     = CHUNK_OVERLAP,
            separators        = ["\n\n", "\n", ".", " ", ""]
        )

    def chunk(self, text: str) -> list[str]:
        chunks = self.splitter.split_text(text)
        return chunks