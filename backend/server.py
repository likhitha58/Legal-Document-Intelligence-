import os
import sys
import json
import time
import re
import numpy as np
import pandas as pd
import faiss
import fitz
import spacy
from uuid import uuid4
from collections import Counter
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
from sentence_transformers import SentenceTransformer
from transformers import T5ForConditionalGeneration, T5Tokenizer
from dotenv import load_dotenv

# Add parent directory to path to import from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def load_large_json(filepath):
    """Load large JSON array file with streaming to avoid MemoryError"""
    print(f"Loading {filepath} with streaming parser...")
    try:
        import ijson
        records = []
        with open(filepath, 'rb') as f:
            for obj in ijson.items(f, 'item'):
                records.append(obj)
                if len(records) % 1000 == 0:
                    print(f"  Loaded {len(records)} records...")
        return pd.DataFrame(records)
    except ImportError:
        # Fallback: manual parsing
        print("  ijson not available, using manual parser...")
        records = []
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Parse JSON array manually
            data = json.loads(content)
            if isinstance(data, list):
                records = data
            else:
                records = [data]
        return pd.DataFrame(records)

# Load classes from demo_rag_engine
from demo_rag_engine import SemanticSearch, RAGPipeline

load_dotenv()

# Custom JSON encoder to handle numpy types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(CustomJSONEncoder, self).default(obj)

app = Flask(__name__, static_folder="../lexai-frontend")
app.json_encoder = CustomJSONEncoder
CORS(app)

# --- Configuration ---
# Look in parent dir for these artifacts as they are generated in the root
EMBEDDINGS_PATH = "../chunk_embeddings.npy"
NLP_JSON_PATH = "../df_final_with_nlp.json"
CONFIG_PATH = "../nlp_model_config.json"

# Global variables for the pipeline
rag_pipeline = None
ner_model = None
uploaded_docs = {}

def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

def chunk_text_chars(text, size=500, overlap=50):
    if not text:
        return []
    chunks = []
    start = 0
    step = max(1, size - overlap)
    text_len = len(text)
    while start < text_len:
        chunk = text[start:start + size].strip()
        if chunk:
            chunks.append(chunk)
        if start + size >= text_len:
            break
        start += step
    return chunks

def extract_entities(text, nlp):
    doc = nlp(text)
    entities = []
    counts = Counter()
    texts = {}
    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char
        })
        counts[ent.label_] += 1
        if ent.label_ not in texts:
            texts[ent.label_] = []
        texts[ent.label_].append(ent.text)
    return entities, dict(counts), texts

def get_ner_model():
    global ner_model
    if ner_model is None:
        ner_model = spacy.load("en_core_web_sm")
    return ner_model

def init_rag():
    global rag_pipeline
    print("Initializing RAG Pipeline...")
    
    # Get absolute paths relative to this script
    base_dir = os.path.dirname(__file__)
    emb_path = os.path.normpath(os.path.join(base_dir, EMBEDDINGS_PATH))
    nlp_path = os.path.normpath(os.path.join(base_dir, NLP_JSON_PATH))
    cfg_path = os.path.normpath(os.path.join(base_dir, CONFIG_PATH))

    if not Path(emb_path).exists() or not Path(nlp_path).exists():
        print(f"Error: NLP artifacts missing at {emb_path} or {nlp_path}. Run activate_lite_pipeline.py first.")
        return False

    # 1. Load Data
    embeddings = np.load(emb_path).astype("float32")
    df_chunks = load_large_json(nlp_path)
    
    with open(cfg_path) as f:
        nlp_config = json.load(f)
    model_name = nlp_config["embedding_model"]["name"]
    embed_model = SentenceTransformer(model_name)
    
    # 2. Build FAISS Index
    embeddings_norm = embeddings.copy()
    faiss.normalize_L2(embeddings_norm)
    faiss_index = faiss.IndexIDMap(faiss.IndexFlatIP(384))
    faiss_index.add_with_ids(embeddings_norm, np.arange(len(embeddings), dtype=np.int64))
    searcher = SemanticSearch(faiss_index, df_chunks, embed_model, embeddings_norm)

    # 3. Configure LLM
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    
    m_name = "google/flan-t5-small"
    tokenizer = T5Tokenizer.from_pretrained(m_name)
    model_offline = T5ForConditionalGeneration.from_pretrained(m_name)
    
    def call_offline(p):
        inputs = tokenizer(p, return_tensors="pt", truncation=True, max_length=512)
        outputs = model_offline.generate(**inputs, max_new_tokens=256, repetition_penalty=1.2)
        return tokenizer.decode(outputs[0], skip_special_tokens=True), "Flan-T5-Small (Offline)"

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            gemini_model = genai.GenerativeModel("gemini-2.5-flash")
            
            def call_llm(p):
                try:
                    res = gemini_model.generate_content(p).text
                    return res, "Gemini 2.5 Flash (Online)"
                except Exception as e:
                    print(f"Gemini failed: {e}. Falling back...")
                    return call_offline(p)
        except Exception as e:
            print(f"Gemini setup failed: {e}. Using offline model.")
            call_llm = call_offline
    else:
        call_llm = call_offline

    rag_pipeline = RAGPipeline(searcher, call_llm, top_k=3)
    print("RAG Pipeline Ready!")
    return True

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/css/<path:path>")
def css_proxy(path):
    return send_from_directory(os.path.join(app.static_folder, "css"), path)

@app.route("/js/<path:path>")
def js_proxy(path):
    return send_from_directory(os.path.join(app.static_folder, "js"), path)

@app.route("/api/query", methods=["POST"])
def query():
    global rag_pipeline
    if not rag_pipeline:
        if not init_rag():
            return jsonify({"error": "RAG pipeline not initialized. Make sure data is processed."}), 500
    
    data = request.json
    question = data.get("question")
    doc_id = data.get("doc_id")
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    try:
        if doc_id:
            doc_data = uploaded_docs.get(doc_id)
            if not doc_data:
                return jsonify({"error": "Invalid doc_id or uploaded document expired"}), 404

            doc_chunks_df = pd.DataFrame(doc_data["chunks"])
            doc_searcher = SemanticSearch(
                doc_data["index"],
                doc_chunks_df,
                rag_pipeline.searcher.embed_model,
                doc_data.get("embeddings_norm")
            )
            doc_rag = RAGPipeline(doc_searcher, rag_pipeline.llm_fn, top_k=rag_pipeline.top_k)
            result = doc_rag.query(question)
        else:
            result = rag_pipeline.query(question)

        # Manually serialize to handle numpy types if json_encoder doesn't catch everything
        return json.dumps(result, cls=CustomJSONEncoder), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/upload", methods=["POST"])
def upload_pdf():
    global rag_pipeline

    if not rag_pipeline:
        if not init_rag():
            return jsonify({"error": "RAG pipeline not initialized. Make sure data is processed."}), 500

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "No file provided"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    try:
        pdf_bytes = file.read()
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages_text = [page.get_text("text") for page in pdf_doc]
        pdf_doc.close()
        extracted_text = clean_text("\n".join(pages_text))
    except Exception:
        return jsonify({"error": "Could not extract text from PDF"}), 400

    if not extracted_text:
        return jsonify({"error": "Could not extract text from PDF"}), 400

    chunks = chunk_text_chars(extracted_text, size=500, overlap=50)
    if not chunks:
        return jsonify({"error": "Could not extract text from PDF"}), 400

    nlp = get_ner_model()
    doc_id = str(uuid4())
    doc_name = file.filename

    chunk_records = []
    for idx, chunk in enumerate(chunks):
        entities, ent_counts, ent_texts = extract_entities(chunk, nlp)
        important_labels = {"ORG", "PERSON", "DATE", "GPE", "LOC", "FAC"}
        filtered_entities = [e for e in entities if e["label"] in important_labels]
        filtered_counts = {k: v for k, v in ent_counts.items() if k in important_labels}
        filtered_texts = {k: v for k, v in ent_texts.items() if k in important_labels}

        chunk_records.append({
            "doc_id": doc_id,
            "contract_name": doc_name,
            "chunk_idx": idx,
            "chunk_text": chunk,
            "ner_entities": filtered_entities,
            "entity_counts": filtered_counts,
            "entity_texts": filtered_texts,
            "clauses_detected": []
        })

    try:
        embeddings = rag_pipeline.searcher.embed_model.encode(
            [c["chunk_text"] for c in chunk_records],
            convert_to_numpy=True
        ).astype("float32")
        embeddings_norm = embeddings.copy()
        faiss.normalize_L2(embeddings_norm)

        doc_index = faiss.IndexIDMap(faiss.IndexFlatIP(384))
        doc_index.add_with_ids(embeddings_norm, np.arange(len(chunk_records), dtype=np.int64))
    except Exception as e:
        return jsonify({"error": f"Failed to index uploaded PDF: {str(e)}"}), 500

    uploaded_docs[doc_id] = {
        "index": doc_index,
        "chunks": chunk_records,
        "name": doc_name,
        "embeddings_norm": embeddings_norm
    }

    return jsonify({
        "doc_id": doc_id,
        "doc_name": doc_name,
        "chunk_count": len(chunk_records),
        "status": "ready"
    })

@app.route("/api/status")
def status():
    return jsonify({
        "status": "ready" if rag_pipeline else "initializing",
        "data_exists": Path(os.path.join(os.path.dirname(__file__), EMBEDDINGS_PATH)).exists()
    })

if __name__ == "__main__":
    init_rag()
    app.run(port=5000)
