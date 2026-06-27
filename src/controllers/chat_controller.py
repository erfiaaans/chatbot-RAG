import json
import os
import random
import re
import time
from datetime import datetime

from flask import Blueprint, Response, jsonify, request

from src.core.rag_pipeline import RAGPipeline

chat_bp = Blueprint("chat", __name__)
rag = RAGPipeline()


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

            # result = rag.dummy_rag_query(question)
            result = rag.rag_query(question)
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


@chat_bp.route("/logs", methods=["GET"])
def get_logs():
    log_data = []
    try:
        if not os.path.exists("rag_log.jsonl"):
            return jsonify({"logs": []}), 200

        with open("rag_log.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    log_data.append(json.loads(line))

        return jsonify({"logs": log_data}), 200
    except Exception as e:
        return jsonify({"error": f"Gagal membaca log: {str(e)}"}), 500


@chat_bp.route("/logs/embedding", methods=["GET"])
def get_logs_embedding():
    log_data = []
    try:
        if not os.path.exists("embedding_log.jsonl"):
            return jsonify({"logs": []}), 200

        with open("embedding_log.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    log_data.append(json.loads(line))

        return jsonify({"logs": log_data}), 200
    except Exception as e:
        return jsonify({"error": f"Gagal membaca log: {str(e)}"}), 500
