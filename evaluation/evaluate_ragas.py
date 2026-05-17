import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
from ragas.dataset_schema import (
    EvaluationDataset, 
    SingleTurnSample
)
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
)

from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.rag_pipeline import RAGPipeline
load_dotenv()
with open("evaluation/test_questions.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)
rag = RAGPipeline()

evaluator_llm = ChatGoogleGenerativeAI(
    model=os.getenv("LLM_MODEL"),
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
)

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
                retrieved_contexts.append(
                    chunk.get("text", "")
                )
            elif hasattr(chunk, "page_content"):
                retrieved_contexts.append(
                    chunk.page_content
                )


        prompt = rag.assembler.assemble(
            retrieved_chunks,
            question,
            []
        )

        answer = rag.generator.generate(prompt)
        print(f"Answer: {answer[:150]}...")
        samples.append(
            SingleTurnSample(
                user_input=question,
                response=answer,
                reference=ground_truth,
                retrieved_contexts=retrieved_contexts,
            )
        )
        time.sleep(15)
    
    except Exception as e:
        print(f"Error processing question: {question}")
        print(f"Error message: {str(e)}")
        continue
    
if len(samples) == 0:
    print("\nTidak ada sample berhasil diproses.")
    print("Kemungkinan quota Gemini habis.")
    exit()
dataset = EvaluationDataset(
    samples=samples
)
print("\n")
print("=" * 60)
print("MENJALANKAN RAGAS")
print("=" * 60)
result = evaluate(
    dataset=dataset,
    metrics=[
        Faithfulness(),
        AnswerRelevancy(),
        ContextPrecision(),
        ContextRecall(),
    ],
    llm=evaluator_llm,
)

print("\n===== RAGAS RESULT =====")
print(result)

result_df = result.to_pandas()
output_path = "evaluation/ragas_result.csv"
result_df.to_csv(output_path, index=False)

print(f"\nHasil evaluasi disimpan ke: {output_path}")