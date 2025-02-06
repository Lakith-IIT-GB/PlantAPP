import os
import asyncio
import requests
from groq import AsyncGroq
from PyPDF2 import PdfReader
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

# Hugging Face API key
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# FAISS index
index = None
all_chunks = []

# Hugging Face model
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"

def process_pdf(pdf_path: str, chunk_size: int = 500) -> List[str]:
    reader = PdfReader(pdf_path)
    all_text = ""
    for page in reader.pages:
        all_text += page.extract_text()
    chunks = [all_text[i:i + chunk_size] for i in range(0, len(all_text), chunk_size)]
    return chunks

def generate_embeddings(chunks: List[str]) -> np.ndarray:
    url = "https://api-inference.huggingface.co/models/sentence-transformers/all-mpnet-base-v2"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    
    embeddings = []
    for chunk in chunks:
        try:
            response = requests.post(url, headers=headers, json={"inputs": chunk})
            if response.status_code == 200:
                embedding = response.json()
                # Convert to numpy array immediately
                embedding_array = np.array(embedding).flatten()
                embeddings.append(embedding_array)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    return np.array(embeddings)

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
        if history is None:
            history = []

        # Get embedding
        url = "https://api-inference.huggingface.co/models/sentence-transformers/all-mpnet-base-v2"
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        response = requests.post(url, headers=headers, json={"inputs": query})
        
        if response.status_code != 200:
            return "Failed to fetch query embedding.", []
            
        # Process embedding
        query_embedding = np.array(response.json()).flatten()
        query_embedding = query_embedding.reshape(1, -1)
        
        # Search
        indices, distances = search_faiss_index(index, query_embedding)
        
        # Get relevant chunks
        top_chunks = []
        if distances[0][0] <= 0.5:  # relevance threshold
            top_chunks = [all_chunks[i] for i in indices[0]]
        
        # Get response
        response, followups = await custom_query_with_groq(query, top_chunks, history)
        return response, followups

    except Exception as e:
        logger.error(f"Error handling query: {e}")
        return "An error occurred while processing your query.", []

async def initialize_rag(pdf_dir: str = "./document", index_file: str = "index_file.faiss"):
    global index, all_chunks
    
    try:
        # Process PDFs
        all_chunks = []
        for filename in os.listdir(pdf_dir):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(pdf_dir, filename)
                chunks = process_pdf(pdf_path)
                all_chunks.extend(chunks)

        # Generate or load index
        if os.path.exists(index_file):
            logger.info("Loading existing FAISS index...")
            index = load_faiss_index(index_file)
        else:
            logger.info("Generating new embeddings and creating FAISS index...")
            embeddings = generate_embeddings(all_chunks)
            if embeddings is None or len(embeddings) == 0:
                raise Exception("Failed to generate embeddings")
                
            # Create and save the index
            index = create_faiss_index(embeddings)
            save_faiss_index(index, index_file)
            logger.info("FAISS index created and saved successfully")
            
    except Exception as e:
        logger.error(f"Error initializing RAG: {e}")
        raise
    
if __name__ == "__main__":
    asyncio.run(initialize_rag())
