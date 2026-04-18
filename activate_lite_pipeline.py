import json
import os
import pandas as pd
import numpy as np
from tqdm import tqdm
from pathlib import Path
from collections import Counter
import spacy
from sentence_transformers import SentenceTransformer

# --- Configuration ---
DATA_PATH = "cuad-main/data/CUADv1.json"
OUTPUT_JSON = "df_final_with_nlp.json"
OUTPUT_EMBEDDINGS = "chunk_embeddings.npy"
OUTPUT_CONFIG = "nlp_model_config.json"
NUM_CONTRACTS = 5  # Lite version
CHUNK_SIZE = 500   # Words
CHUNK_OVERLAP = 50

# --- Helper Functions ---

def clean_text(text):
    if not text: return ""
    # Basic cleaning
    import re
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    for i in range(0, len(words), size - overlap):
        chunk = " ".join(words[i:i + size])
        chunks.append(chunk)
        if i + size >= len(words): break
    return chunks

# From extracted_code.py
CUAD_CLAUSE_TYPES = {
    "Effective Date": ["effective date", "commencement date", "execution date", "date of this agreement"],
    "Termination": ["termination", "terminate", "expiration", "expire", "end of term"],
    "Confidentiality / Non-Disclosure": ["confidentiality", "confidential", "non-disclosure", "nda", "secret", "proprietary"],
    "Payment Terms": ["payment", "consideration", "fee", "charge", "salary", "wages", "compensation"],
    "Indemnification": ["indemnify", "indemnification", "hold harmless", "indemnity"],
    "Governing Law": ["governing law", "jurisdiction", "venue", "applicable law", "state law"],
    "Entire Agreement": ["entire agreement", "supersede", "integration clause"],
    "Warranties": ["warranty", "warrant", "warrants", "representations and warranties"],
    "Assignment": ["assignment", "assign", "transfer", "shall not be assigned"],
    "Severability": ["severability", "severability clause", "if any provision"],
    "Entry Into Force": ["entry into force", "enters into effect", "becomes effective"],
    "Counterparts": ["counterpart", "facsimile", "signature", "signed"],
    "Data Protection": ["data protection", "gdpr", "privacy", "personal data", "gdpr"],
    "Limitation of Liability": ["limitation of liability", "liable", "liability", "damages", "consequential"],
    "Representations": ["represent", "representation", "represent and warrant"],
    "Insurance": ["insurance", "insure", "policy", "coverage"],
    "Force Majeure": ["force majeure", "act of god", "unforeseeable circumstances"],
    "Amendment / Modification": ["amendment", "amendment clause", "modify", "modification"],
    "Binding Effect": ["binding", "binding upon", "binds", "bind"],
    "Dispute Resolution": ["dispute", "arbitration", "mediation", "resolution"],
    "Intellectual Property": ["intellectual property", "copyright", "patent", "trademark", "ip"],
    "Publicity / Announcements": ["publicity", "announcement", "announcement rights", "public"],
    "Contact Information": ["contact", "notice", "address", "telephone", "email"],
    "Notices": ["notice", "written notice", "notify", "notification"],
    "Waiver": ["waiver", "waive", "waived"],
    "Relationship": ["relationship", "agent", "partnership", "joint venture"],
    "Termination for Cause": ["termination for cause", "cause", "material breach"],
    "Survival": ["survival", "survive", "surviving"],
    "Definitions": ["definition", "defined as", "means"],
    "Clause":  ["clause", "section", "provision", "article"],
    "Limitation on Damages": ["limitation on damages", "cap", "maximum liability"],
    "Insurance Coverage": ["insurance coverage", "covered", "coverage limits"],
    "Indemnity": ["indemnity", "indemnify", "indemnified"],
    "Additional Considerations": ["additional", "further", "supplementary"],
    "Post-Termination": ["post-termination", "after termination", "following termination"],
    "Materials": ["materials", "documentation", "documents", "records"],
    "Warranty Disclaimer": ["warranty disclaimer", "no warranty", "as is"],
    "Obligations": ["obligation", "obligated", "shall", "must"],
    "Licenses": ["license", "licensed", "licensing"],
}

CLAUSE_KEYWORDS = {}
for clause_type, keywords in CUAD_CLAUSE_TYPES.items():
    for keyword in keywords:
        CLAUSE_KEYWORDS[keyword.lower()] = clause_type

def detect_clauses(text):
    text_lower = text.lower()
    clauses = set()
    matches = {}
    for kw, ct in CLAUSE_KEYWORDS.items():
        if kw in text_lower:
            clauses.add(ct)
            if ct not in matches: matches[ct] = []
            matches[ct].append(kw)
    return list(clauses), matches

def extract_entities(text, nlp):
    doc = nlp(text)
    entities = []
    counts = Counter()
    texts = {}
    for ent in doc.ents:
        entities.append({"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char})
        counts[ent.label_] += 1
        if ent.label_ not in texts: texts[ent.label_] = []
        texts[ent.label_].append(ent.text)
    return entities, dict(counts), texts

# --- Main Pipeline ---

def main():
    print(f"Starting Lite NLP Pipeline for {NUM_CONTRACTS} contracts...")
    
    if not os.path.exists(DATA_PATH):
        print(f"Error: Data file not found at {DATA_PATH}")
        return

    with open(DATA_PATH, 'r') as f:
        data = json.load(f)

    contracts = data['data'][:NUM_CONTRACTS]
    
    print("Loading models...")
    nlp = spacy.load("en_core_web_sm")
    embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    
    all_chunks_data = []
    
    for doc_idx, doc in enumerate(tqdm(contracts, desc="Processing contracts")):
        contract_title = doc.get('title', f"Contract_{doc_idx}")
        # Combine all paragraphs
        full_text = " ".join([p.get('context', '') for p in doc.get('paragraphs', [])])
        clean_full_text = clean_text(full_text)
        chunks = chunk_text(clean_full_text)
        
        for chunk_idx, chunk in enumerate(chunks):
            entities, ent_counts, ent_texts = extract_entities(chunk, nlp)
            clauses, matches = detect_clauses(chunk)
            
            all_chunks_data.append({
                "doc_id": doc_idx,
                "contract_name": contract_title,
                "chunk_idx": chunk_idx,
                "chunk_text": chunk,
                "ner_entities": entities,
                "entity_counts": ent_counts,
                "entity_texts": ent_texts,
                "clauses_detected": clauses,
                "clause_counts": {c: len(m) for c, m in matches.items()},
                "matched_keywords": matches
            })

    print(f"Generated {len(all_chunks_data)} chunks. Generating embeddings...")
    texts = [c['chunk_text'] for c in all_chunks_data]
    embeddings = embedding_model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    
    # Add embeddings as list to JSON data
    for i, chunk in enumerate(all_chunks_data):
        chunk['embedding'] = embeddings[i].tolist()
    
    print("Saving outputs...")
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(all_chunks_data, f, indent=2)
    
    np.save(OUTPUT_EMBEDDINGS, embeddings)
    
    config = {
        "ner_model": {"name": "spacy en_core_web_sm"},
        "embedding_model": {"name": "sentence-transformers/all-MiniLM-L6-v2", "dimension": 384},
        "processing_stats": {"total_contracts": NUM_CONTRACTS, "total_chunks": len(all_chunks_data)}
    }
    with open(OUTPUT_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)
        
    print("Lite Pipeline Complete!")
    print(f"Files generated: {OUTPUT_JSON}, {OUTPUT_EMBEDDINGS}, {OUTPUT_CONFIG}")

if __name__ == "__main__":
    main()
