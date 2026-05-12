from flask import Flask, render_template
from dotenv import load_dotenv
from src.controllers.chat_controller import chat_bp
from src.ingestion.ingestion_pipeline import IngestionPipeline
from src.config.config import settings

load_dotenv()

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("landing-page.html")

@app.route("/chatbot")
def chatbot():
    return render_template("landing-page.html")

app.register_blueprint(chat_bp, url_prefix="/api")

# Inisialisasi dokumen saat startup
ingestor = IngestionPipeline()
documents = ingestor.loader.load_folder("./data")
result = ingestor.run_documents(documents=documents, overwrite=False)
print(result)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
