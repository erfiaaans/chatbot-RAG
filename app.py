from flask import Flask
from dotenv import load_dotenv
from src.controllers.chat_controller import chat_bp
from src.ingestion.ingestion_pipeline import IngestionPipeline
from src.config import settings

load_dotenv()

app = Flask(__name__)
app.register_blueprint(chat_bp)

# Inisialisasi dokumen saat startup
ingestor = IngestionPipeline()
documents = ingestor.loader.load_folder("./data")
result = ingestor.run_documents(documents=documents, overwrite=False)
print(result)

# documents = ingestor.loader.load("./documents/Skripsi/KB_PEDOMAN_SKRIPSI_BAB I.md")
# result = ingestor.run_documents(documents=[documents])
# paths = [
#     "./documents/Skripsi/bab1.md",
#     "./documents/Magang/laporan1.md"
# ]
# documents = [ingestor.loader.load(p) for p in paths]
# result = ingestor.run_documents(documents)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
