import time
import sys
import os
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
# from ragas.metrics import (
#     Faithfulness,
#     AnswerRelevancy,
#     ContextPrecision,
#     ContextRecall,
# )
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
    answer_similarity,
)

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)
from langchain_core.messages import HumanMessage
from src.core.rag_pipeline import RAGPipeline
load_dotenv()
with open("evaluation/test_questions.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)
rag = RAGPipeline()

evaluator_llm = ChatGoogleGenerativeAI(
    model=os.getenv("LLM_MODEL"),
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
    convert_system_message_to_human=True,
)

evaluator_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY"),
)
wrapped_llm = LangchainLLMWrapper(evaluator_llm)
wrapped_emb = LangchainEmbeddingsWrapper(evaluator_embeddings)

print("=" * 60)
print("Mengecek koneksi LLM...")
try:
    from langchain_core.messages import HumanMessage
    test_response = evaluator_llm.invoke([HumanMessage(content="Halo")])
    print(f"LLM OK: {test_response.content[:50]}")
except Exception as e:
    print(f"LLM GAGAL: {e}")
    exit()
    
print("Mengecek koneksi Embeddings...")
try:
    test_emb = evaluator_embeddings.embed_query("test")
    print(f"  Embeddings OK: dimensi={len(test_emb)}")
except Exception as e:
    print(f"  Embeddings GAGAL: {e}")
    exit()

print("Mengecek wrapped LLM...")
async def test_wrapped():
    try:
        from ragas.llms.base import BaseRagasLLM
        from langchain_core.prompt_values import StringPromptValue
        result = await wrapped_llm.agenerate_text(
            StringPromptValue(text="Halo, jawab singkat saja.")
        )
        print(f"  Wrapped LLM OK: {result.generations[0][0].text[:50]}")
    except Exception as e:
        print(f"  Wrapped LLM ERROR: {type(e).__name__}: {e}")

asyncio.run(test_wrapped())
  
samples = []
print("=" * 60)
print("Starting RAGAS evaluation...")
print("=" * 60)

for idx, item in enumerate(test_data):
    question = item["question"]
    ground_truth = item["ground_truth"]

    try:
        print(f"\n[{idx + 1}/{len(test_data)}]")
        print(f"Processing question: {question}")
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
            print(f"  SKIP: contexts kosong untuk pertanyaan ini")
            continue


        prompt = rag.assembler.assemble(
            retrieved_chunks,
            question,
            []
        )

        answer = rag.generator.generate(prompt)
        if not answer or not answer.strip():
            print(f"  SKIP: answer kosong untuk pertanyaan ini")
            continue

        print(f"  Answer: {answer[:150]}...")
        print(f"  Contexts ditemukan: {len(retrieved_contexts)} chunk")
        samples.append(
            # SingleTurnSample(
                {
                    "question": str(question),          
                    "answer": str(answer),               
                    "contexts": retrieved_contexts,      
                    "ground_truth": str(ground_truth),
                }
            # )
        )
        time.sleep(15)
    
    except Exception as e:
        print(f"Error processing question: {question}")
        print(f"Error message: {str(e)}")
        continue
    
if len(samples) == 0:
    print("\nTidak ada sample berhasil diproses.")
    print("Kemungkinan quota Gemini habis atau semua contexts kosong.")
    exit()
# dataset = EvaluationDataset(
#     samples=samples
# )
print(f"\nTotal sample berhasil: {len(samples)}")

# FIX: debug cek format data sebelum evaluate
print("\n" + "=" * 60)
print("DEBUG FULL SAMPLE")
print("=" * 60)
for i, s in enumerate(samples):
    print(f"\nSample {i + 1}:")
    print(f"  question     : ({type(s['question']).__name__}) '{s['question']}'")
    print(f"  answer       : ({type(s['answer']).__name__}) '{s['answer'][:100]}'")
    print(f"  ground_truth : ({type(s['ground_truth']).__name__}) '{s['ground_truth']}'")
    print(f"  contexts     : ({type(s['contexts']).__name__}) {len(s['contexts'])} item")
    for j, ctx in enumerate(s['contexts']):
        print(f"    [{j}] ({type(ctx).__name__}) '{ctx[:80]}'")
# ===================== DEBUG TEST METRIK MANUAL =====================
print("\n" + "=" * 60)
print("DEBUG TEST METRIK MANUAL (sample pertama)")
print("=" * 60)

async def test_metrics_manual():
    row = {
        "question": samples[0]["question"],
        "answer": samples[0]["answer"],
        "contexts": samples[0]["contexts"],
        "ground_truth": samples[0]["ground_truth"],
    }

    metrics_to_test = [
        ("faithfulness", faithfulness),
        ("answer_relevancy", answer_relevancy),
        ("context_precision", context_precision),
        ("context_recall", context_recall),
        ("answer_correctness", answer_correctness),
        ("answer_similarity", answer_similarity),
    ]

    for name, metric in metrics_to_test:
        try:
            metric.llm = wrapped_llm
            if hasattr(metric, "embeddings"):
                metric.embeddings = wrapped_emb
            score = await metric.ascore(row)
            print(f"  {name}: {score}")
        except Exception as e:
            print(f"  {name}: ERROR -> {e}")

asyncio.run(test_metrics_manual())

dataset = Dataset.from_list(samples)
print("\n")
print("=" * 60)
print("MENJALANKAN RAGAS")
print("=" * 60)
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
)

print("\n===== RAGAS RESULT =====")
print(result)

result_df = result.to_pandas()
output_path = "evaluation/ragas_result.csv"
result_df.to_csv(output_path, index=False)

print(f"\nHasil evaluasi disimpan ke: {output_path}")