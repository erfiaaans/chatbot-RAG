import asyncio
import json
import os
import sys
import time
from typing import List

from dotenv import load_dotenv
from pydantic.v1 import SecretStr

# Path setup agar bisa melakukan import dari root direktori 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datasets import Dataset
from langchain_core.embeddings import Embeddings
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    answer_correctness,
    answer_relevancy,
    answer_similarity,
    context_precision,
    context_recall,
    faithfulness,
)

from src.core.rag_pipeline import RAGPipeline
from src.services.embedding_service import EmbeddingService


# ==========================================
# 1. KELAS ADAPTER UNTUK EMBEDDING LOKAL
# ==========================================
class LocalLangchainEmbeddings(Embeddings):
    def __init__(self, embedding_service: EmbeddingService):
        self.service = embedding_service

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Proses batch teks menjadi list of vector (list of float)
        return self.service.model.encode(texts).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.service.embed_query(text)


# ==========================================
# KELAS INTERCEPTOR UNTUK FIX BUG RAGAS + GEMINI
# ==========================================
class SafeGemini(ChatGoogleGenerativeAI):
    def generate(self, *args, **kwargs):
        kwargs.pop("temperature", None)
        return super().generate(*args, **kwargs)

    async def agenerate(self, *args, **kwargs):
        kwargs.pop("temperature", None)
        return await super().agenerate(*args, **kwargs)


# ==========================================
# 2. SETUP & INISIALISASI
# ==========================================
load_dotenv()

with open("evaluation/test_questions.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)

print("Menginisialisasi RAG Pipeline...")
rag = RAGPipeline()

print("Menginisialisasi LLM Evaluator (Gemini)...")
api_key = os.getenv("GEMINI_API_KEY")
evaluator_llm = SafeGemini(
    model=os.getenv("LLM_MODEL", "gemini-pro"),
    google_api_key=SecretStr(api_key) if api_key else None,
    client_options=None,
    transport=None,
    additional_headers=None,
    client=None,
)

print("Menginisialisasi Local Embeddings Evaluator...")
my_embedding_service = EmbeddingService()
evaluator_embeddings = LocalLangchainEmbeddings(my_embedding_service)

wrapped_llm = LangchainLLMWrapper(evaluator_llm)
wrapped_emb = LangchainEmbeddingsWrapper(evaluator_embeddings)

# ==========================================
# 3. PENGECEKAN KONEKSI & MODEL
# ==========================================
print("=" * 60)
print("Mengecek koneksi LLM...")
try:
    test_response = evaluator_llm.invoke([HumanMessage(content="Halo")])
    print(f"LLM OK: {test_response.content[:50]}")
except Exception as e:
    print(f"LLM GAGAL: {e}")
    exit()

print("Mengecek koneksi Local Embeddings...")
try:
    test_emb = evaluator_embeddings.embed_query("test")
    print(f"  Embeddings OK: dimensi={len(test_emb)}")
except Exception as e:
    print(f"  Embeddings GAGAL: {e}")
    exit()

print("Mengecek wrapped LLM (Async)...")


print("Mengecek wrapped LLM (Async)...")


async def test_wrapped():
    try:
        from langchain_core.prompt_values import StringPromptValue

        result = await wrapped_llm.agenerate_text(
            StringPromptValue(text="Halo, jawab singkat saja.")  # type: ignore
        )
        print(f"  Wrapped LLM OK: {result.generations[0][0].text[:50]}")
    except Exception as e:
        print(f"  Wrapped LLM ERROR: {type(e).__name__}: {e}")


asyncio.run(test_wrapped())


asyncio.run(test_wrapped())

# ==========================================
# 4. GENERATE JAWABAN (RAG PIPELINE)
# ==========================================
samples = []
print("\n" + "=" * 60)
print("Memulai Proses Retrieval & Generation...")
print("=" * 60)

for idx, item in enumerate(test_data):
    question = item["question"]
    ground_truth = item["ground_truth"]

    try:
        print(f"\n[{idx + 1}/{len(test_data)}]")
        print(f"Processing question: {question}")

        # 4.1 RETRIEVE
        retrieved_chunks = rag.retriever.retrieve(question)
        retrieved_contexts = []
        for chunk in retrieved_chunks:
            if isinstance(chunk, dict):
                text = chunk.get("text", "").strip()
            elif hasattr(chunk, "page_content"):
                text = chunk.page_content.strip()
            else:
                text = str(chunk).strip()

            if text:
                retrieved_contexts.append(text)

        if not retrieved_contexts:
            print("  SKIP: contexts kosong untuk pertanyaan ini")
            continue

        # 4.2 ASSEMBLE PROMPT
        prompt = rag.assembler.assemble(retrieved_chunks, question, [])

        # 4.3 GENERATE JAWABAN
        answer = rag.generator.generate(prompt)
        if not answer or not answer.strip():
            print("  SKIP: answer kosong untuk pertanyaan ini")
            continue

        print(f"  Answer: {answer[:150]}...")
        print(f"  Contexts ditemukan: {len(retrieved_contexts)} chunk")

        # 4.4 SIMPAN KE SAMPLE UNTUK RAGAS
        samples.append(
            {
                "question": str(question),
                "answer": str(answer),
                "contexts": retrieved_contexts,
                "ground_truth": str(ground_truth),
            }
        )
        # Jeda : Rate Limit Gemini API
        time.sleep(15)

    except Exception as e:
        print(f"Error processing question: {question}")
        print(f"Error message: {str(e)}")
        continue

if len(samples) == 0:
    print("\nTidak ada sample berhasil diproses.")
    print("Kemungkinan quota Gemini habis atau semua contexts kosong.")
    exit()

print(f"\nTotal sample berhasil: {len(samples)}")

# ==========================================
# 5. DEBUGGING SAMPEL RAGAS
# ==========================================
print("\n" + "=" * 60)
print("DEBUG FULL SAMPLE")
print("=" * 60)
for i, s in enumerate(samples):
    print(f"\nSample {i + 1}:")
    print(f"  question     : ({type(s['question']).__name__}) '{s['question']}'")
    print(f"  answer       : ({type(s['answer']).__name__}) '{s['answer'][:100]}...'")
    print(
        f"  ground_truth : ({type(s['ground_truth']).__name__}) '{s['ground_truth']}'"
    )
    print(
        f"  contexts     : ({type(s['contexts']).__name__}) {len(s['contexts'])} item"
    )

# ==========================================
# 6. EKSEKUSI EVALUASI RAGAS
# ==========================================
# Ubah dict ke format HuggingFace Dataset
dataset = Dataset.from_list(samples)

print("\n" + "=" * 60)
print("MENJALANKAN RAGAS EVALUATION")
print("=" * 60)
print("Proses ini akan mengevaluasi jawaban menggunakan metrik Ragas...")
print("Metrik Vektor (Relevancy/Similarity) akan diproses LOKAL.")

result = evaluate(
    dataset=dataset,
    metrics=[
        context_precision,
        faithfulness,
        answer_relevancy,
        context_recall,
        answer_correctness,
        answer_similarity,
    ],
    llm=evaluator_llm,
    embeddings=evaluator_embeddings,
    raise_exceptions=False,
    is_async=False,
)

print("\n===== RAGAS RESULT =====")
print(result)

# ==========================================
# 7. MENYIMPAN HASIL KE CSV
# ==========================================
result_df = result.to_pandas()
output_path = "evaluation/ragas_result.csv"
result_df.to_csv(output_path, index=False)  # type: ignore
print(f"\nHasil evaluasi disimpan ke: {output_path}")
