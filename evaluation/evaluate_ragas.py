import nest_asyncio

nest_asyncio.apply()
import asyncio
import json
import os
import sys
import time
from typing import List

import pandas as pd  # Tambahkan ini untuk mengolah data akhir
from dotenv import load_dotenv
from pydantic.v1 import SecretStr
from tabulate import tabulate

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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

PROGRESS_FILE = "evaluation/progress.json"
OUTPUT_CSV = "evaluation/ragas_result.csv"
TEST_QUESTIONS_FILE = "evaluation/test_questions.json"

SLEEP_GENERATE = int(os.getenv("SLEEP_GENERATE", "20"))
SLEEP_EVAL = int(os.getenv("SLEEP_EVAL", "60"))

my_answer_relevancy = answer_relevancy.__class__(strictness=1)

ALL_METRICS = [
    context_precision,
    faithfulness,
    context_recall,
    answer_correctness,
    my_answer_relevancy,
    answer_similarity,
]

METRIC_COLS = [
    "context_precision",
    "faithfulness",
    "context_recall",
    "answer_correctness",
    "answer_relevancy",
    "answer_similarity",
]


class LocalLangchainEmbeddings(Embeddings):
    def __init__(self, embedding_service: EmbeddingService):
        self.service = embedding_service

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            embedding = self.service.embed(text)
            embeddings.append(embedding)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        Mengubah query tunggal menjadi embedding.
        """
        return self.service.embed_query(text)


# ==========================================
# CUSTOM LLM WRAPPER DENGAN LOGGING DETAIL
# ==========================================
LLM_CALL_COUNT = 0


class SafeGemini(ChatGoogleGenerativeAI):
    def _log_call(self, args):
        global LLM_CALL_COUNT
        LLM_CALL_COUNT += 1
        prompt_text = str(args).lower()

        if "halo" in prompt_text and "jawab singkat" in prompt_text:
            tahap = "CEK KONEKSI LLM"
        elif "halo" in prompt_text:
            tahap = "CEK KONEKSI LLM"
        elif "statements" in prompt_text or "faithful" in prompt_text:
            tahap = "EVALUASI: Faithfulness"
        elif (
            "question for the given answer" in prompt_text or "relevancy" in prompt_text
        ):
            tahap = "EVALUASI: Answer Relevancy"
        elif "useful" in prompt_text and "context" in prompt_text:
            tahap = "EVALUASI: Context Precision"
        elif "analyze each sentence" in prompt_text or "attributed" in prompt_text:
            tahap = "EVALUASI: Context Recall"
        elif (
            "ground truth" in prompt_text
            or "correctness" in prompt_text
            or "factual overlap" in prompt_text
        ):
            tahap = "EVALUASI: Answer Correctness"
        else:
            tahap = "INFERENSI: RAG Generate Jawaban"

        print(f"[LOG LLM] Panggilan ke-{LLM_CALL_COUNT:<3} | {tahap}")

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self._log_call(messages)
        kwargs.pop("temperature", None)
        return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        self._log_call(messages)
        kwargs.pop("temperature", None)
        return await super()._agenerate(
            messages, stop=stop, run_manager=run_manager, **kwargs
        )


# ==========================================
# PROGRESS SAVING
# ==========================================
def load_progress() -> list[dict]:
    if os.path.exists(PROGRESS_FILE):
        if os.path.getsize(PROGRESS_FILE) == 0:
            print("Progress file kosong, memulai dari awal.")
            return []
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(
                f"Melanjutkan progress: {len(data)} sample sudah tersimpan/dievaluasi."
            )
            return data
        except json.JSONDecodeError:
            print("Progress file formatnya tidak valid (rusak), memulai dari awal.")
            return []
    return []


def save_progress(samples: list[dict]):
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)


def clear_progress(force=False):
    """Menghapus file progress HANYA jika parameter force=True"""
    if force:
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
            print("\nProgress file dihapus (force=True).")
    else:
        print("\nProgress file dipertahankan (force=False).")


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

    return True


# ==========================================
# TAHAP 1: GENERATE JAWABAN (RAG PIPELINE)
# ==========================================
def extract_text_from_chunk(chunk) -> str:
    if isinstance(chunk, dict):
        return chunk.get("text", "").strip()
    if hasattr(chunk, "page_content"):
        return chunk.page_content.strip()
    return str(chunk).strip()


def generate_samples(
    rag: RAGPipeline, test_data: list[dict], existing_samples: list[dict]
) -> list[dict]:
    done_questions = {s["question"] for s in existing_samples}
    samples = list(existing_samples)

    remaining = [item for item in test_data if item["question"] not in done_questions]
    total = len(test_data)

    print(
        f"\n[TAHAP 1] GENERASI JAWABAN | Total: {total} | Selesai: {len(done_questions)} | Sisa: {len(remaining)}"
    )
    print("=" * 60)

    for item in remaining:
        question = item["question"]
        ground_truth = item["ground_truth"]
        idx = next(i for i, d in enumerate(test_data) if d["question"] == question)

        print(f"\n[{idx + 1}/{total}] {question}")
        try:
            retrieved_chunks = rag.retriever.retrieve(question)
            contexts = [
                text
                for chunk in retrieved_chunks
                if (text := extract_text_from_chunk(chunk))
            ]

            if not contexts:
                print("  SKIP: contexts kosong")
                samples.append(
                    {
                        "question": str(question),
                        "answer": "Informasi tidak ditemukan.",
                        "contexts": [],
                        "ground_truth": str(ground_truth),
                    }
                )
                save_progress(samples)
                continue

            prompt = rag.assembler.assemble(retrieved_chunks, question, [])
            response = rag.generator.generate(prompt)
            answer = response.text or ""

            if not answer or not answer.strip():
                print("  SKIP: answer kosong")
                continue

            print(f"  Answer: {answer[:150]}...")
            print(f"  Contexts: {len(contexts)} chunk")

            samples.append(
                {
                    "question": str(question),
                    "answer": str(answer),
                    "contexts": contexts,
                    "ground_truth": str(ground_truth),
                }
            )
            save_progress(samples)

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

        time.sleep(SLEEP_GENERATE)

    return samples


def main():
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
        temperature=0.0,  # [PERBAIKAN] Pastikan output selalu deterministik dan JSON murni
    )

    print("Menginisialisasi Local Embeddings...")
    evaluator_embeddings = LocalLangchainEmbeddings(EmbeddingService())
    wrapped_llm = LangchainLLMWrapper(evaluator_llm)
    wrapped_emb = LangchainEmbeddingsWrapper(evaluator_embeddings)

    ok = asyncio.run(
        check_connections(evaluator_llm, evaluator_embeddings, wrapped_llm)
    )
    if not ok:
        sys.exit(1)

    existing_samples = load_progress()
    samples = generate_samples(rag, test_data, existing_samples)

    if not samples:
        print("\nTidak ada sample berhasil diproses.")
        sys.exit(1)

    # ==========================================
    # TAHAP 2: EVALUASI SATU PER SATU
    # ==========================================
    print("\n" + "=" * 60)
    print("[TAHAP 2] MENJALANKAN RAGAS EVALUATION (PER PERTANYAAN)")
    print("=" * 60)

    for idx, item in enumerate(samples):
        if all(m in item for m in METRIC_COLS):
            print(
                f"[{idx + 1}/{len(samples)}] SKIP: Metrik sudah lengkap untuk Q: {item['question'][:50]}..."
            )
            continue

        print(f"\n[{idx + 1}/{len(samples)}] Mengevaluasi: {item['question']}")

        single_dataset = Dataset.from_list(
            [
                {
                    "question": item["question"],
                    "answer": item["answer"],
                    "contexts": item["contexts"],
                    "ground_truth": item["ground_truth"],
                }
            ]
        )

        try:
            from ragas.run_config import RunConfig

            custom_config = RunConfig(
                max_retries=2, max_wait=60, timeout=120, max_workers=1
            )

            result = evaluate(
                dataset=single_dataset,
                metrics=ALL_METRICS,
                llm=wrapped_llm,
                embeddings=wrapped_emb,
                raise_exceptions=True,
                run_config=custom_config,
                is_async=False,
            )

            raw_df = result.to_pandas()
            if isinstance(raw_df, pd.DataFrame):
                res_df = raw_df
            else:
                res_df = pd.concat(raw_df, ignore_index=True)

            for col in METRIC_COLS:
                if col in res_df.columns:
                    val = res_df.iloc[0][col]
                    item[col] = float(val) if pd.notna(val) else 0.0
                else:
                    item[col] = 0.0

            save_progress(samples)
            q_text = item["question"]
            q_short = q_text if len(q_text) <= 50 else q_text[:47] + "..."
            print(
                f"  [Q: {q_short}]\n"
                f"  [SKOR] " + " | ".join([f"{c}: {item[c]:.2f}" for c in METRIC_COLS])
            )

            time.sleep(SLEEP_EVAL)

        except Exception as e:
            # Jika sekarang gagal, terminal akan menampilkan error yang sesungguhnya (bukan sekadar 0.0 diam-diam)
            print(f"  ERROR Evaluasi Ragas: {type(e).__name__} - {e}")
            continue

    # ==========================================
    # TAHAP 3: REKAPITULASI & SIMPAN CSV
    # ==========================================
    print("\n" + "=" * 80)
    print("===== HASIL EVALUASI PER PERTANYAAN =====")
    print("=" * 80)

    table_data = []

    for idx, item in enumerate(samples):
        q_text = item.get("question", "")
        q_short = q_text if len(q_text) <= 20 else q_text[:17] + "..."

        row = [idx + 1, q_short] + [f"{item.get(c, 0.0):.2f}" for c in METRIC_COLS]
        table_data.append(row)

    headers = ["No", "Question"] + METRIC_COLS

    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    # 2. Cetak rata-rata keseluruhan
    print("\n" + "=" * 60)
    print("===== RATA-RATA KESELURUHAN =====")
    print("=" * 60)

    final_df = pd.DataFrame(samples)

    for col in METRIC_COLS:
        if col in final_df.columns:
            avg = final_df[col].mean()
            print(f"  {col:<25}: {avg:.4f}")

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    final_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nHasil lengkap berhasil disimpan ke: {OUTPUT_CSV}")
    clear_progress(force=False)


if __name__ == "__main__":
    main()
