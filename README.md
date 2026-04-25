# LexAI: Legal Document Intelligence System

LexAI is a high-performance, RAG-based (Retrieval-Augmented Generation) intelligence system designed for automated contract review and legal document analysis. It combines semantic vector search (FAISS), Named Entity Recognition (spacy), and Large Language Models (Gemini/Flan-T5) to provide precise answers to complex legal queries.

## 🌟 Key Features
- **Semantic Search**: Uses `all-MiniLM-L6-v2` embeddings to find relevant contract clauses beyond simple keyword matching.
- **RAG Pipeline**: Integrates context-aware generation to provide grounded answers with source citations.
- **Hybrid LLM Backend**: Supports Google Gemini (Online) for superior reasoning and Flan-T5 (Offline) as a reliable local fallback.
- **Premium UI**: A modern, glassmorphism-inspired web interface for seamless interaction.

---

## 🏗️ Folder Structure
```text
Legal-Document-Intelligence/
├── backend/
│   └── server.py              # Flask API server & integration logic
├── lexai-frontend/            # Premium Web Frontend
│   ├── css/
│   │   └── style.css          # Modern glassmorphism styling
│   ├── js/
│   │   └── app.js             # Frontend logic & API integration
│   └── index.html             # Main entry point
├── cuad-main/                 # Dataset & training scripts
│   └── data/
│       └── CUADv1.json        # Contract Understanding Atticus Dataset
├── activate_lite_pipeline.py  # Data processing & embedding generation script
├── demo_rag_engine.py         # CLI-based demonstration of the RAG logic
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

---

## ⚙️ Working Pipeline

1. **Data Pre-processing**: Contracts are loaded from the CUAD dataset, cleaned, and split into manageable chunks.
2. **NLP Enrichment**: Each chunk undergoes Named Entity Recognition (NER) to detect parties, dates, and locations, and keyword matching to identify specific legal clauses (e.g., Termination, Indemnification).
3. **Embedding Generation**: Text chunks are converted into 384-dimensional vectors using Sentence Transformers.
4. **Vector Indexing**: Embeddings are stored in a FAISS index for high-speed similarity search.
5. **RAG Execution**:
   - User asks a question (e.g., "What are the payment terms?").
   - System retrieves the top-K most relevant chunks from the FAISS index.
   - A prompt is constructed with the retrieved context and the user question.
   - The LLM generates a grounded answer citing the source document.

---

## 🚀 How to Run

### 1. Prerequisites
Ensure you have Python 3.8+ installed. Install the required dependencies:
```powershell
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Prepare the Data
Generate the NLP artifacts and vector index (this only needs to be done once):
```powershell
python activate_lite_pipeline.py
```
*Note: This will generate `df_final_with_nlp.json`, `chunk_embeddings.npy`, and `nlp_model_config.json`.*

### 3. (Optional) Configure Gemini API
For high-quality answers, create a `.env` file in the root directory:
```text
GEMINI_API_KEY=your_api_key_here
```

### 4. Start the Application
Run the backend server:
```powershell
python backend/server.py
```
Access the interface at: **`http://localhost:5000`**

---

## 📊 Output Format

### API Response (`/api/query`):
```json
{
  "question": "What is the governing law?",
  "answer": "The agreement is governed by the laws of the State of New York.",
  "sources": [
    {
      "doc_id": 1,
      "name": "Promotion Agreement",
      "idx": 8,
      "score": 0.85
    }
  ],
  "llm_backend": "Gemini 1.5 Flash (Online)",
  "total_ms": 450.5
}
```

---

## ⚖️ License
This project is for educational and research purposes using the CUAD dataset.
