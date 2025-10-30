# rag_memory.py
import sqlite3
import numpy as np
import faiss
from openai import OpenAI
import os
import pickle
from config import OPENAI_API_KEY

DB_PATH = "viabilities.db"
EMBEDDING_DIM = 1536  # depende do modelo usado (ex: text-embedding-3-small)

# Corrigir a leitura da chave de API
api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("A chave OPENAI_API_KEY não foi encontrada. Configure a variável de ambiente ou passe diretamente no arquivo config.py.")

client = OpenAI(api_key=api_key)

# --------------------------
# 1. Inicializar DB
# --------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS viabilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        client_name TEXT,
        viability_type TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed BOOLEAN DEFAULT 0,
        file_path TEXT,
        summary TEXT,
        llm_feedback TEXT,
        overall_score REAL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS embeddings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        viability_id INTEGER,
        chunk_text TEXT,
        embedding BLOB,
        FOREIGN KEY (viability_id) REFERENCES viabilities(id)
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        viability_id INTEGER,
        role TEXT,
        message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (viability_id) REFERENCES viabilities(id)
    )
    """)
    conn.commit()
    conn.close()

# --------------------------
# 2. Gerar embedding
# --------------------------
def generate_embedding(text: str) -> np.ndarray:
    print(f"Gerando embedding para o texto: {text[:100]}...")  # Log do texto (primeiros 100 caracteres)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    embedding = np.array(response.data[0].embedding, dtype="float32")
    print(f"Embedding gerado: {embedding}")  # Log do embedding gerado
    return embedding

# --------------------------
# 3. Salvar viabilidade e embeddings
# --------------------------
def save_viability(title, client_name, viability_type, text, file_path):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO viabilities (title, client_name, viability_type, file_path) VALUES (?, ?, ?, ?)",
        (title, client_name, viability_type, file_path)
    )
    vid = cur.lastrowid

    # dividir texto em chunks (~500 tokens)
    chunks = [text[i:i+1500] for i in range(0, len(text), 1500)]
    for c in chunks:
        emb = generate_embedding(c)
        cur.execute(
            "INSERT INTO embeddings (viability_id, chunk_text, embedding) VALUES (?, ?, ?)",
            (vid, c, pickle.dumps(emb))
        )
    conn.commit()
    conn.close()
    return vid

# --------------------------
# 4. Busca RAG (similaridade)
# --------------------------
def search_similar(text_query, top_k=3):
    print("Iniciando busca de casos semelhantes...")  # Log inicial

    # Conectar ao banco de dados
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, embedding, chunk_text, viability_id FROM embeddings")
    rows = cur.fetchall()
    conn.close()

    # Verificar se há embeddings na base
    if not rows:
        print("Nenhum embedding encontrado na base de dados.")
        return []

    print(f"Total de embeddings encontrados: {len(rows)}")  # Log do número de embeddings

    # Preparar FAISS index
    embeddings = [pickle.loads(r[1]) for r in rows]  # Deserializar os embeddings
    print(f"Primeiro embedding carregado: {embeddings[0]}")  # Log do primeiro embedding
    matrix = np.vstack(embeddings)  # Criar matriz de embeddings
    index = faiss.IndexFlatL2(EMBEDDING_DIM)  # Índice FAISS
    index.add(matrix)
    print("FAISS index criado e embeddings adicionados.")  # Log após criar o índice

    # Gerar embedding da consulta
    query_emb = generate_embedding(text_query)
    print(f"Embedding da consulta gerado: {query_emb}")  # Log do embedding da consulta

    # Realizar a busca
    distances, indices = index.search(np.array([query_emb]), top_k)
    print(f"Distâncias retornadas: {distances}")  # Log das distâncias
    print(f"Índices retornados: {indices}")  # Log dos índices

    # Recuperar os resultados
    results = []
    for i, idx in enumerate(indices[0]):
        r = rows[idx]
        results.append({
            "viability_id": r[3],
            "chunk_text": r[2],
            "distance": float(distances[0][i])
        })
    print(f"Resultados encontrados: {results}")  # Log dos resultados finais
    return results


