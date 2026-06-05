import os

from dotenv import load_dotenv
from flask import Flask, render_template
from sentence_transformers import SentenceTransformer
from src.controllers.chat_controller import chat_bp
from src.ingestion.ingestion_pipeline import IngestionPipeline

load_dotenv()
app = Flask(__name__)
app.register_blueprint(chat_bp, url_prefix="/api")


def initialize_system():
    print("--- Memeriksa status dokumen... ---")
    ingestor = IngestionPipeline()

    data_path = "./data"
    if not os.path.exists(data_path) or not os.listdir(data_path):
        print("Folder data kosong, melewati ingestion.")
        return

    documents = ingestor.loader.load_folder(data_path)
    result = ingestor.run_documents(documents=documents, overwrite=False)
    print(f"--- Ingestion selesai: {result} ---")


#  Routes
@app.route("/")
@app.route("/chatbot")
def index():
    return render_template("landing-page.html")


@app.route("/cara-penggunaan")
def cara_penggunaan():
    return render_template("cara-penggunaan.html")


if __name__ == "__main__":
    initialize_system()

    print("--- Server berjalan di http://127.0.0.1:5000 ---")
    app.run(debug=True, use_reloader=False)
