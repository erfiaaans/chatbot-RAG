import json
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

from src.core.rag_pipeline import RAGPipeline
with open("evaluation/test_questions.json", "r", encoding="utf-8") as f:
    test_data = json.load(f)
rag = RAGPipeline()

questions = []
answers = []
contexts = []
ground_truths = []


for item in test_data:
    question = item["question"]
    ground_truth = item["ground_truth"]

    retrieved_chunks = rag.retriever.retrieve(question)

    retrieved_contexts = [
        chunk.get("text", "")
        for chunk in retrieved_chunks
    ]


    prompt = rag.assembler.assemble(
        retrieved_chunks,
        question,
        []
    )

    answer = rag.generator.generate(prompt)

    questions.append(question)
    answers.append(answer)
    contexts.append(retrieved_contexts)
    ground_truths.append(ground_truth)

    print(f"Question : {question}")
    print(f"Answer   : {answer}")
    print("=" * 60)

dataset = Dataset.from_dict({
    "question": questions,
    "answer": answers,
    "contexts": contexts,
    "ground_truth": ground_truths,
})

result = evaluate(
    dataset=dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    ],
)

print("\n===== RAGAS RESULT =====")
print(result)

result_df = result.to_pandas()
result_df.to_csv("evaluation/ragas_result.csv", index=False)

print("\nHasil evaluasi disimpan ke:")
print("evaluation/ragas_result.csv")