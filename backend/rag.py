import os
import asyncio
from groq import AsyncGroq
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import logging
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables and initialize Groq client
load_dotenv()
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize global variables
embedding_model = SentenceTransformer("all-mpnet-base-v2")
index = None
all_chunks = []

def process_pdf(pdf_path: str, chunk_size: int = 500) -> List[str]:
    reader = PdfReader(pdf_path)
    all_text = ""
    for page in reader.pages:
        all_text += page.extract_text()
    chunks = [all_text[i:i + chunk_size] for i in range(0, len(all_text), chunk_size)]
    return chunks

def generate_embeddings(chunks: List[str]) -> np.ndarray:
    return np.array(embedding_model.encode(chunks))

def create_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

def search_faiss_index(index: faiss.IndexFlatL2, query_embedding: np.ndarray, top_k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    return index.search(query_embedding, top_k)

def save_faiss_index(index: faiss.IndexFlatL2, file_path: str) -> None:
    faiss.write_index(index, file_path)

def load_faiss_index(file_path: str) -> faiss.IndexFlatL2:
    return faiss.read_index(file_path)

async def custom_query_with_groq(query: str, relevant_chunks: List[str], history: List[Dict[str, str]] = None) -> Tuple[str, List[str]]:
    try:
        if history is None:
            history = []
            
        context = "\n".join(relevant_chunks) if relevant_chunks else ""
        
        messages = history.copy()
        messages.append({
            "role": "system",
            "content": f"You are a helpful assistant. Use this context to inform your response:\n{context}"
        })
        messages.append({
            "role": "user",
            "content": query
        })
        
        completion = await client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        response = completion.choices[0].message.content
        
        followup_prompt = f"Based on the conversation history and current query '{query}', suggest 3 relevant follow-up questions."
        followup_completion = await client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": followup_prompt}],
            temperature=0.7,
            max_tokens=150
        )
        
        followups = [q.strip() for q in followup_completion.choices[0].message.content.split("\n") if q.strip()]
        return response, followups[:3]
        
    except Exception as e:
        logger.error(f"Error in custom_query_with_groq: {e}")
        raise

async def handle_query(query: str, history: List[Dict[str, str]] = None) -> Tuple[str, List[str]]:
    try:
        query_embedding = embedding_model.encode([query]).reshape(1, -1)
        indices, distances = search_faiss_index(index, query_embedding)
        
        relevance_threshold = 0.5
        if distances[0][0] > relevance_threshold:
            top_chunks = []
        else:
            top_chunks = [all_chunks[i] for i in indices[0]]
            
        response, followups = await custom_query_with_groq(query, top_chunks, history)
        return response, followups
        
    except Exception as e:
        logger.error(f"Error handling query: {e}")
        return "An error occurred while processing your query.", []

async def initialize_rag(pdf_dir: str = "./document", index_file: str = "index_file.faiss"):
    global index, all_chunks
    
    try:
        # Process PDFs
        for filename in os.listdir(pdf_dir):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(pdf_dir, filename)
                chunks = process_pdf(pdf_path)
                all_chunks.extend(chunks)

        # Generate or load index
        if os.path.exists(index_file):
            index = load_faiss_index(index_file)
        else:
            embeddings = generate_embeddings(all_chunks)
            index = create_faiss_index(embeddings)
            save_faiss_index(index, index_file)
            
    except Exception as e:
        logger.error(f"Error initializing RAG: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(initialize_rag())