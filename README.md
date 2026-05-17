# 🚀 Chatbot RAG – Intelligent Document-Based QA System

> Chatbot cerdas berbasis **Retrieval-Augmented Generation (RAG)** yang mampu menjawab pertanyaan secara akurat berdasarkan dokumen yang diberikan.

---

## ✨ Overview

Proyek ini mengimplementasikan sistem **Question Answering berbasis dokumen** dengan menggabungkan:

- 🔎 **Semantic Search (Embedding)**
- 🧠 **Large Language Model (LLM)**
- 📦 **Vector Database (ChromaDB)**

Berbeda dengan chatbot biasa, sistem ini **tidak hanya mengandalkan pengetahuan model**, tetapi juga mengambil informasi langsung dari dokumen → sehingga jawaban lebih **relevan, spesifik, dan kontekstual**.

---

## 🔥 Key Features

- 📄 **Document-Aware AI** → Jawaban berbasis dokumen nyata
- ⚡ **Fast Retrieval** → Menggunakan vector similarity search
- 🧩 **Modular Pipeline** → Mudah dikembangkan & scalable
- 🧠 **Contextual Answering** → Mengurangi halusinasi LLM
- 🔄 **End-to-End RAG Pipeline**

---

## 🧠 How It Works

```id="flow1"
User Question
     ↓
Embedding Query
     ↓
Vector Search (ChromaDB)
     ↓
Retrieve Relevant Chunks
     ↓
LLM Generation
     ↓
Final Answer
```

Sistem bekerja dengan menggabungkan **retrieval + generation**, sehingga menghasilkan jawaban yang lebih akurat dibanding chatbot biasa.

---

## 🏗️ Project Architecture

```id="flow2"
chatbot-rag/
│
├── app.py                  # Main app
├── rag_pipeline.py         # Core RAG logic
├── ingestion_pipeline.py   # Data indexing pipeline
│
├── document_loader.py      # Load documents
├── text_chunker.py         # Text splitting
├── embedding service.py    # Embedding generation
├── vector_store.py         # Vector database (ChromaDB)
├── retriever.py            # Similarity search
├── generator.py            # LLM response generator
│
├── templates/              # Frontend (HTML)
├── static/                 # CSS/JS
│
├── documents/              # ❌ Not included
├── chroma_db/              # ❌ Not included
```

## 🛠️ Tech Stack

- **Python**
- **ChromaDB** (Vector Database)
- **OpenAI API / LLM**
- **Flask / FastAPI** (optional)

## 👨‍💻 Author

## **ERFIA NADIA SAFARI**

## Run

```
uv sync
uv run python app.py
python evaluation/evaluate_ragas.py
```
