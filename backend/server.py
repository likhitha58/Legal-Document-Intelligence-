import os
import sys
import json
import time
import numpy as np
import pandas as pd
import faiss
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
from sentence_transformers import SentenceTransformer
from transformers import T5ForConditionalGeneration, T5Tokenizer
from dotenv import load_dotenv

# Add parent directory to path to import from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
    df_chunks = pd.read_json(nlp_path, orient="records")
    
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
            gemini_model = genai.GenerativeModel("gemini-1.5-flash")
            
            def call_llm(p):
                try:
                    res = gemini_model.generate_content(p).text
                    return res, "Gemini 1.5 Flash (Online)"
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
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    try:
        result = rag_pipeline.query(question)
        # Manually serialize to handle numpy types if json_encoder doesn't catch everything
        return json.dumps(result, cls=CustomJSONEncoder), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/status")
def status():
    return jsonify({
        "status": "ready" if rag_pipeline else "initializing",
        "data_exists": Path(os.path.join(os.path.dirname(__file__), EMBEDDINGS_PATH)).exists()
    })

if __name__ == "__main__":
    init_rag()
    app.run(port=5000)
