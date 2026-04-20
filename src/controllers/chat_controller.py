import json
import time
import re
import random
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, Response

from src.core.rag_pipeline import RAGPipeline

chat_bp = Blueprint("chat", __name__)
rag = RAGPipeline()


@chat_bp.route("/")
def index():
    return render_template("index.html")


@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.json
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Pertanyaan tidak boleh kosong."}), 400

    start_time = datetime.now().strftime("%H:%M")
    start = time.time()

    def generate():
        try:
            time.sleep(random.uniform(0.2, 0.6))
            yield f"data: {json.dumps({'meta': {'time': start_time}}, ensure_ascii=False)}\n\n"

            result = rag.dummy_rag_query(question)
            answer = result["answer"]
            sources = result.get("sources", [])

            for token in re.findall(r"\S+|\s+", answer):
                yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
                delay = (
                    0.12
                    if token in [",", ".", "?", "!", ":"]
                    else random.uniform(0.01, 0.03)
                )
                time.sleep(delay)

            yield f"data: {json.dumps({'sources': sources}, ensure_ascii=False)}\n\n"

            duration_ms = int((time.time() - start) * 1000)
            yield f"data: {json.dumps({'done': True, 'meta': {'latency_ms': duration_ms}}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return Response(generate(), content_type="text/event-stream")


@chat_bp.route("/reset", methods=["POST"])
def reset():
    rag.reset_history()
    return jsonify({"status": "Riwayat percakapan direset."})
