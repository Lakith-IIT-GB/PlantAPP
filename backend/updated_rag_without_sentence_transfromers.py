import os
import asyncio
from groq import AsyncGroq
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

# Global variables
index = None
all_chunks = []

# Load precomputed FAISS index
def load_faiss_index(file_path: str) -> faiss.IndexFlatL2:
    return faiss.read_index(file_path)

# Load text chunks from a saved file
def load_text_chunks(file_path: str) -> List[str]:
    with open(file_path, "r", encoding="utf-8") as file:
        return [chunk.strip() for chunk in file.read().split("\n---\n") if chunk.strip()]

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
        query_embedding = np.load("query_embedding.npy")  # Load precomputed query embeddings
        query_embedding = query_embedding.reshape(1, -1)
        indices, distances = index.search(query_embedding, 5)
        
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

async def initialize_rag(index_file: str = "index_file.faiss", chunks_file: str = "text_chunks.txt"):
    global index, all_chunks
    try:
        index = load_faiss_index(index_file)  # Load FAISS index
        all_chunks = load_text_chunks(chunks_file)  # Load text chunks
    except Exception as e:
        logger.error(f"Error initializing RAG: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(initialize_rag())