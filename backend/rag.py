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
        text = page.extract_text()
        if text:
            all_text += text + "\n"

    chunks = [all_text[i:i + chunk_size] for i in range(0, len(all_text), chunk_size)]
    return chunks

def generate_embeddings(chunks: List[str]) -> np.ndarray:
    return np.array(embedding_model.encode(chunks))

def create_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

def save_faiss_index(index: faiss.IndexFlatL2, file_path: str) -> None:
    faiss.write_index(index, file_path)

def load_faiss_index(file_path: str) -> faiss.IndexFlatL2:
    return faiss.read_index(file_path)

def save_query_embeddings_batch(chunks: List[str], output_file: str = "precomputed_embeddings.npy"):
    """Save embeddings for all chunks to use later."""
    embeddings = embedding_model.encode(chunks)
    np.save(output_file, embeddings)
    return embeddings

async def preprocess_and_save():
    """Run this function locally to generate all necessary files."""
    global index, all_chunks
    
    try:
        # Process PDFs and get chunks
        pdf_dir = "./document"
        all_chunks = []
        for filename in os.listdir(pdf_dir):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(pdf_dir, filename)
                chunks = process_pdf(pdf_path)
                all_chunks.extend(chunks)

        # Save chunks to file
        with open("text_chunks.txt", "w", encoding="utf-8") as f:
            for chunk in all_chunks:
                f.write(chunk + "\n---\n")  # Add separator between chunks

        # Generate and save embeddings
        embeddings = save_query_embeddings_batch(all_chunks)
        
        # Create and save FAISS index
        index = create_faiss_index(embeddings)
        save_faiss_index(index, "index_file.faiss")
        
        logger.info("Successfully saved all preprocessing files")
        
    except Exception as e:
        logger.error(f"Error in preprocessing: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(preprocess_and_save())