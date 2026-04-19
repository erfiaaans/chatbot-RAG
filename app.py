import os
from flask             import Flask, request, jsonify, render_template
from rag_pipeline      import RAGPipeline
from ingestion_pipeline import IngestionPipeline

app      = Flask(__name__)
rag      = RAGPipeline()
ingestor = IngestionPipeline()

UPLOAD_FOLDER = "./documents"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data     = request.json
    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "Pertanyaan tidak boleh kosong."}), 400
    result = rag.query(question)
    return jsonify({
        "answer"  : result["answer"],
        "sources" : result["sources"]
    })

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

@app.route("/reset", methods=["POST"])
def reset():
    rag.reset_history()
    return jsonify({"status": "Riwayat percakapan direset."})

if __name__ == "__main__":
    app.run(debug=True)