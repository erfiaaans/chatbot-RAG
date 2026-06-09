import nest_asyncio
nest_asyncio.apply()
import asyncio
import json
import os
import sys
import time
import argparse
from typing import List, Optional

from dotenv import load_dotenv
from pydantic.v1 import SecretStr

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

PROGRESS_FILE = "evaluation/progress.json"
OUTPUT_CSV = "evaluation/ragas_result.csv"
TEST_QUESTIONS_FILE = "evaluation/test_questions.json"

SLEEP_GENERATE = int(os.getenv("SLEEP_GENERATE", "20"))
SLEEP_EVAL = int(os.getenv("SLEEP_EVAL", "30"))

# LLM_METRICS = [
#     context_precision,   # ~2 req/sampel
#     faithfulness,        # ~2 req/sampel
#     context_recall,      # ~2 req/sampel
#     answer_correctness,  # ~2 req/sampel
# ]
ALL_METRICS = [
    context_precision,
    faithfulness,
    context_recall,
    answer_correctness,
    answer_relevancy,
    answer_similarity,
]

# EMBEDDING_METRICS = [
#     answer_relevancy,
#     answer_similarity,
# ]
class LocalLangchainEmbeddings(Embeddings):
    def __init__(self, embedding_service: EmbeddingService):
        self.service = embedding_service

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.service.model.encode(texts).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.service.embed_query(text)

class SafeGemini(ChatGoogleGenerativeAI):
    """Hapus parameter 'temperature' yang tidak diterima Gemini API."""
    def generate(self, *args, **kwargs):
        kwargs.pop("temperature", None)
        return super().generate(*args, **kwargs)

    async def agenerate(self, *args, **kwargs):
        kwargs.pop("temperature", None)
        return await super().agenerate(*args, **kwargs)

# ==========================================
# PROGRESS SAVING (supaya tidak ulang dari awal kalau crash)
# ==========================================
def load_progress() -> list[dict]:
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Melanjutkan progress: {len(data)} sample sudah tersimpan.")
        return data
    return []


def save_progress(samples: list[dict]):
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)


def clear_progress():
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        
# ==========================================
# CEK KONEKSI
# ==========================================
async def check_connections(evaluator_llm, evaluator_embeddings, wrapped_llm):
    print("=" * 60)

    print("Mengecek koneksi LLM...")
    try:
        resp = evaluator_llm.invoke([HumanMessage(content="Halo")])
        print(f"  LLM OK: {resp.content[:50]}")
    except Exception as e:
        print(f"  LLM GAGAL: {e}")
        return False

    print("Mengecek Local Embeddings...")
    try:
        emb = evaluator_embeddings.embed_query("test")
        print(f"  Embeddings OK: dimensi={len(emb)}")
    except Exception as e:
        print(f"  Embeddings GAGAL: {e}")
        return False

    print("Mengecek wrapped LLM (Async)...")
    try:
        from langchain_core.prompt_values import StringPromptValue
        result = await wrapped_llm.agenerate_text(
            StringPromptValue(text="Halo, jawab singkat saja.")
        )
        print(f"  Wrapped LLM OK: {result.generations[0][0].text[:50]}")
    except Exception as e:
        print(f"  Wrapped LLM ERROR: {type(e).__name__}: {e}")

    return True

# ==========================================
# GENERATE JAWABAN (RAG PIPELINE)
# ==========================================
def extract_text_from_chunk(chunk) -> str:
    if isinstance(chunk, dict):
        return chunk.get("text", "").strip()
    if hasattr(chunk, "page_content"):
        return chunk.page_content.strip()
    return str(chunk).strip()


def generate_samples(rag: RAGPipeline, test_data: list[dict], existing_samples: list[dict]) -> list[dict]:
    done_questions = {s["question"] for s in existing_samples}
    samples = list(existing_samples)

    remaining = [item for item in test_data if item["question"] not in done_questions]
    total = len(test_data)

    print(f"\nTotal pertanyaan: {total} | Sudah diproses: {len(done_questions)} | Sisa: {len(remaining)}")
    print("=" * 60)

    for item in remaining:
        question = item["question"]
        ground_truth = item["ground_truth"]
        idx = next(i for i, d in enumerate(test_data) if d["question"] == question)

        print(f"\n[{idx + 1}/{total}] {question}")
        try:
            retrieved_chunks = rag.retriever.retrieve(question)
            contexts = [
                text for chunk in retrieved_chunks
                if (text := extract_text_from_chunk(chunk))
            ]

            if not contexts:
                print("  SKIP: contexts kosong")
                continue

            prompt = rag.assembler.assemble(retrieved_chunks, question, [])
            answer = rag.generator.generate(prompt)

            if not answer or not answer.strip():
                print("  SKIP: answer kosong")
                continue

            print(f"  Answer: {answer[:150]}...")
            print(f"  Contexts: {len(contexts)} chunk")

            samples.append({
                "question": str(question),
                "answer": str(answer),
                "contexts": contexts,
                "ground_truth": str(ground_truth),
            })

            save_progress(samples)

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        time.sleep(SLEEP_GENERATE)

    return samples

def main():
    # if sys.platform == "win32":
    #     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    load_dotenv()

    with open(TEST_QUESTIONS_FILE, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    print("Menginisialisasi RAG Pipeline...")
    rag = RAGPipeline()

    print("Menginisialisasi LLM Evaluator (Gemini)...")
    api_key = os.getenv("GEMINI_API_KEY")
    evaluator_llm = SafeGemini(
        model=os.getenv("LLM_MODEL", "gemini-2.0-flash"),
        google_api_key=SecretStr(api_key) if api_key else None,
        client_options=None,
        transport="rest",
        additional_headers=None,
        client=None,
    )

    print("Menginisialisasi Local Embeddings...")
    evaluator_embeddings = LocalLangchainEmbeddings(EmbeddingService())

    wrapped_llm = LangchainLLMWrapper(evaluator_llm)
    wrapped_emb = LangchainEmbeddingsWrapper(evaluator_embeddings)

    ok = asyncio.run(check_connections(evaluator_llm, evaluator_embeddings, wrapped_llm))
    if not ok:
        sys.exit(1)

    existing_samples = load_progress()
    samples = generate_samples(rag, test_data, existing_samples)

    if not samples:
        print("\nTidak ada sample berhasil diproses.")
        sys.exit(1)

    print(f"\nTotal sample berhasil: {len(samples)}")

    print("\n" + "=" * 60)
    print("MENJALANKAN RAGAS EVALUATION")
    print("=" * 60)

    dataset = Dataset.from_list(samples)

    from ragas.run_config import RunConfig
    result = evaluate(
        dataset=dataset,
        metrics=ALL_METRICS,
        llm=wrapped_llm,
        embeddings=wrapped_emb,
        raise_exceptions=False,
        run_config=RunConfig(
            max_retries=10,
            max_wait=120,
            timeout=300,
        )
    )

    result_df = result.to_pandas()

    print("\n===== RAGAS RESULT (PER PERTANYAAN) =====")
    metric_cols = [
        "context_precision",
        "faithfulness",
        "context_recall",
        "answer_correctness",
        "answer_relevancy",
        "answer_similarity",
    ]

    for idx, row in result_df.iterrows():
        print(f"\n[{idx + 1}] {row['question']}")
        for col in metric_cols:
            if col in row:
                val = row[col]
                val_str = f"{val:.4f}" if val == val else "N/A"  # cek NaN
                print(f"  {col:<25}: {val_str}")

    print("\n===== RATA-RATA SEMUA PERTANYAAN =====")
    for col in metric_cols:
        if col in result_df.columns:
            avg = result_df[col].mean()
            print(f"  {col:<25}: {avg:.4f}")

    # Simpan ke CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    result_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nHasil disimpan ke: {OUTPUT_CSV}")

    clear_progress()
    print("Progress file dihapus.")


if __name__ == "__main__":
    main()
