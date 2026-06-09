import os
import threading

from dotenv import load_dotenv
from flask import Flask, render_template

from src.controllers.chat_controller import chat_bp
from src.ingestion.ingestion_pipeline import IngestionPipeline

load_dotenv()
app = Flask(__name__)
app.register_blueprint(chat_bp, url_prefix="/api")


init_lock = threading.Lock()
is_initialized = False


def initialize_system():
    global is_initialized

    with init_lock:
        if is_initialized:
            return

        print("--- Memeriksa status dokumen... ---")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_dir, "data")

        if not os.path.exists(data_path) or not os.listdir(data_path):
            print("Folder data kosong, melewati ingestion.")
            is_initialized = True
            return

        try:
            ingestor = IngestionPipeline()
            documents = ingestor.loader.load_folder(data_path)
            result = ingestor.run_documents(documents=documents, overwrite=False)
            print(f"--- Ingestion selesai: {result} ---")
            is_initialized = True
        except Exception as e:
            print(f"--- Terjadi kesalahan saat Ingestion: {e} ---")


#  Routes
@app.route("/")
@app.route("/chatbot")
def index():
    return render_template("landing-page.html")


@app.route("/cara-penggunaan")
def cara_penggunaan():
    return render_template("cara-penggunaan.html")


initialize_system()
if __name__ == "__main__":
    print("--- Server berjalan di http://127.0.0.1:5000 ---")
    app.run(debug=True, use_reloader=False)
