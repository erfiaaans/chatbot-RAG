import os
import json
import time
import re
import random
from datetime import datetime
from flask import Flask, request, jsonify, render_template, Response

from rag_pipeline import RAGPipeline
from ingestion_pipeline import IngestionPipeline

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

rag = RAGPipeline()
ingestor = IngestionPipeline()
documents = ingestor.loader.load_folder("./documents")
result = ingestor.run_documents(
    documents=documents, overwrite=False, doc_id="akademik_tif_2026"
)

# documents = ingestor.loader.load_folder("./documents/Skripsi/KB_PEDOMAN_SKRIPSI_BAB II.md")
# result = ingestor.run_documents([documents])
# paths = [
#     "./documents/Skripsi/bab1.md",
#     "./documents/Magang/laporan1.md"
# ]
# documents = [ingestor.loader.load(p) for p in paths]
# result = ingestor.run_documents(documents)


UPLOAD_FOLDER = "./documents"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


# ==============================
# STREAMING CHAT (SSE)
# ==============================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    question = data.get("question", "").strip()

    if not question:
        return jsonify({"error": "Pertanyaan tidak boleh kosong."}), 400

    start_time = datetime.now().strftime("%H:%M")
    start = time.time()

    def generate():
        try:
            # fake thinking
            time.sleep(random.uniform(0.2, 0.6))

            # kirim TIME saja di awal
            yield f"data: {json.dumps({'meta': {'time': start_time}}, ensure_ascii=False)}\n\n"

            result = rag.dummy_rag_query(question)
            answer = result["answer"]
            sources = result.get("sources", [])

            tokens = re.findall(r"\S+|\s+", answer)

            for token in tokens:
                yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"

                if token in [",", ".", "?", "!", ":"]:
                    time.sleep(0.12)
                else:
                    time.sleep(random.uniform(0.01, 0.03))

            yield f"data: {json.dumps({'sources': sources}, ensure_ascii=False)}\n\n"

            duration_ms = int((time.time() - start) * 1000)

            yield f"data: {json.dumps({'done': True, 'meta': {'latency_ms': duration_ms}}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return Response(generate(), content_type="text/event-stream")


# ==============================
# UPLOAD
# ==============================
@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "File tidak ditemukan."}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".docx", ".md"]:
        return jsonify({"error": "Format tidak didukung."}), 400

    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    result = ingestor.run(path)
    return jsonify(result)


# ==============================
# RESET
# ==============================
@app.route("/reset", methods=["POST"])
def reset():
    rag.reset_history()
    return jsonify({"status": "Riwayat percakapan direset."})


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
