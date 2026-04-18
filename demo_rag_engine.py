import os
import json
import time
import warnings
import datetime
from pathlib import Path
from textwrap import dedent

import numpy as np
import pandas as pd
from tqdm import tqdm

# FAISS for vector search
import faiss

# Sentence Transformers for query embedding
from sentence_transformers import SentenceTransformer

# Transformers for offline LLM (Flan-T5)
from transformers import T5ForConditionalGeneration, T5Tokenizer

# Load environment variables from .env if present
from dotenv import load_dotenv
load_dotenv()

warnings.filterwarnings("ignore")

# --- Configuration ---
EMBEDDINGS_PATH = "chunk_embeddings.npy"
NLP_JSON_PATH = "df_final_with_nlp.json"
CONFIG_PATH = "nlp_model_config.json"
FAISS_INDEX_PATH = "legal_faiss.index"

# --- Classes ---

class SemanticSearch:
    def __init__(self, faiss_idx, chunk_df, embed_model, embeddings_norm):
        self.faiss_idx       = faiss_idx
        self.chunk_df        = chunk_df.reset_index(drop=True)
        self.embed_model     = embed_model
        self.embeddings_norm = embeddings_norm

    def _encode_query(self, query: str) -> np.ndarray:
        vec = self.embed_model.encode([query], convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(vec)
        return vec

    def search_with_metadata(self, query: str, top_k: int = 5) -> list:
        query_vec = self._encode_query(query)
        scores, ids = self.faiss_idx.search(query_vec, k=top_k)
        results = []
        for rank, (chunk_id, score) in enumerate(zip(ids[0], scores[0]), start=1):
            if chunk_id == -1: continue
            row = self.chunk_df.iloc[chunk_id]
            results.append({
                "rank"       : rank,
                "chunk_id"   : int(chunk_id),
                "score"      : float(score),
                "doc_id"     : row.get("doc_id", ""),
                "contract_name": row.get("contract_name", "Unknown"),
                "chunk_idx"  : int(row.get("chunk_idx", 0)),
                "chunk_text" : str(row.get("chunk_text", "")),
                "clauses_detected": row.get("clauses_detected", []),
                "entity_counts": row.get("entity_counts", {})
            })
        return results

class RAGPipeline:
    SYSTEM_PROMPT = dedent("""\
        You are a legal document analysis assistant specializing in contract review.
        Your task is to answer the user's question based ONLY on the provided contract excerpts.
        Rules:
        - Answer using only information from the context below.
        - Be concise and precise. Use bullet points for lists.
        - If the context does not contain a clear answer, say: "The provided contracts do not specify this information."
        - Always cite the source document ID at the end of your answer.
        - Do not invent or assume information not present in the context.
    """)

    def __init__(self, searcher: SemanticSearch, llm_fn, top_k: int = 5):
        self.searcher  = searcher
        self.llm_fn    = llm_fn
        self.top_k     = top_k

    def query(self, question: str) -> dict:
        t_start = time.time()
        
        # 1. Retrieve
        t_retrieve = time.time()
        chunks = self.searcher.search_with_metadata(question, top_k=self.top_k)
        retrieval_ms = (time.time() - t_retrieve) * 1000

        # 2. Build prompt
        context_blocks = []
        for chunk in chunks:
            clauses_str = ", ".join(chunk.get("clauses_detected", [])[:3]) or "General"
            block = (
                f"[Source: {chunk['contract_name']} ({chunk['doc_id']}) | Chunk {chunk['chunk_idx']} | "
                f"Relevance: {chunk['score']:.3f} | Clauses: {clauses_str}]\n"
                f"{chunk['chunk_text']}"
            )
            context_blocks.append(block)
        
        context_str = "\n\n---\n\n".join(context_blocks)
        prompt = f"{self.SYSTEM_PROMPT}\n\nCONTRACT EXCERPTS:\n{context_str}\n\nQUESTION: {question}\n\nANSWER:"

        # 3. Generate
        t_gen = time.time()
        raw_answer, used_backend = self.llm_fn(prompt)
        generation_ms = (time.time() - t_gen) * 1000

        # 4. Post-process
        answer = raw_answer.strip()
        for prefix in ["ANSWER:", "Answer:", "A:"]:
            if answer.startswith(prefix): answer = answer[len(prefix):].strip()

        return {
            "question": question,
            "answer": answer,
            "sources": [{"doc_id": c["doc_id"], "name": c["contract_name"], "idx": c["chunk_idx"], "score": round(c["score"], 4)} for c in chunks],
            "retrieval_ms": round(retrieval_ms, 1),
            "generation_ms": round(generation_ms, 1),
            "total_ms": round((time.time() - t_start) * 1000, 1),
            "llm_backend": used_backend
        }

def main():
    print("=" * 70)
    print("  ⚖️  LEGAL RAG DEMO ENGINE")
    print("=" * 70)

    # 1. Load Data
    print("\n[1/4] Loading NLP artifacts...")
    if not Path(EMBEDDINGS_PATH).exists() or not Path(NLP_JSON_PATH).exists():
        print("Error: NLP artifacts missing. Run activate_lite_pipeline.py first.")
        return

    embeddings = np.load(EMBEDDINGS_PATH).astype("float32")
    df_chunks = pd.read_json(NLP_JSON_PATH, orient="records")
    
    with open(CONFIG_PATH) as f:
        nlp_config = json.load(f)
    model_name = nlp_config["embedding_model"]["name"]
    embed_model = SentenceTransformer(model_name)
    
    # 2. Build FAISS Index
    print("[2/4] Initializing FAISS Vector Index...")
    embeddings_norm = embeddings.copy()
    faiss.normalize_L2(embeddings_norm)
    faiss_index = faiss.IndexIDMap(faiss.IndexFlatIP(384))
    faiss_index.add_with_ids(embeddings_norm, np.arange(len(embeddings), dtype=np.int64))
    searcher = SemanticSearch(faiss_index, df_chunks, embed_model, embeddings_norm)
    print(f"      OK: Index contains {faiss_index.ntotal} vectors.")

    # 3. Configure LLM
    print("[3/4] Configuring LLM Backend...")
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    
    print("      Loading offline FLAN-T5-Small as primary/fallback...")
    m_name = "google/flan-t5-small"
    tokenizer = T5Tokenizer.from_pretrained(m_name)
    model_offline = T5ForConditionalGeneration.from_pretrained(m_name)
    
    def call_offline(p):
        inputs = tokenizer(p, return_tensors="pt", truncation=True, max_length=512)
        # Increased max_new_tokens to 256 and added repetition_penalty for better legal answers
        outputs = model_offline.generate(**inputs, max_new_tokens=256, repetition_penalty=1.2)
        return tokenizer.decode(outputs[0], skip_special_tokens=True), "Flan-T5-Small (Offline)"

    if api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            # Switching to gemini-2.0-flash-lite which often has more generous free tier limits
            gemini_model = genai.GenerativeModel("gemini-2.0-flash-lite")
            backend_name = "Gemini 2.0 Flash-Lite (Online)"
            
            def call_llm(p):
                try:
                    res = gemini_model.generate_content(p).text
                    return res, backend_name
                except Exception as e:
                    print(f"      [LLM Error] Gemini failed: {e}. Falling back...")
                    return call_offline(p)
            print(f"      OK: {backend_name} configured.")
        except Exception as e:
            print(f"      [Setup Error] Gemini failed: {e}. Using offline model.")
            call_llm = call_offline
    else:
        print("      No Gemini API key found. Using offline model.")
        call_llm = call_offline

    rag = RAGPipeline(searcher, call_llm, top_k=2)

    # 4. Demonstrate Queries
    print("\n[4/4] Running Demonstration Queries...")
    demo_questions = [
        "What are the termination conditions?",
        "What is the governing law and jurisdiction?",
        "What are the confidentiality obligations?"
    ]

    for i, q in enumerate(demo_questions, 1):
        print("\n" + "-"*70)
        print(f"QUERY {i}: {q}")
        print("-"*70)
        print("      Thinking...")
        res = rag.query(q)
        print(f"🤖 ANSWER ({res['llm_backend']}):")
        print(f"   {res['answer']}")
        print(f"\n📄 SOURCES:")
        for s in res['sources']:
            print(f"   • {s['name']} | score: {s['score']}")
        print(f"\n⏱  Latency: {res['total_ms']}ms (Ret: {res['retrieval_ms']}ms, Gen: {res['generation_ms']}ms)")

    print("\n" + "="*70)
    print("  [SUCCESS] RAG Demo Complete!")
    print("="*70)

if __name__ == "__main__":
    main()
