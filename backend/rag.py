import os
import asyncio
from groq import AsyncGroq
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

# Step 1: PDF Chunking and Embedding
def process_pdf(pdf_path, chunk_size=500):
    """
    Extracts text from a PDF, splits it into chunks, and returns a list of chunks.
    """
    reader = PdfReader(pdf_path)
    all_text = ""
    for page in reader.pages:
        all_text += page.extract_text()

    # Split text into chunks
    chunks = [all_text[i:i + chunk_size] for i in range(0, len(all_text), chunk_size)]
    return chunks

def generate_embeddings(chunks, embedding_model):
    """
    Generates embeddings for the chunks using a specified model.
    """
    embeddings = embedding_model.encode(chunks)
    return np.array(embeddings)

# Step 2: FAISS Indexing and Retrieval
def create_faiss_index(embeddings):
    """
    Creates and returns a FAISS index from the given embeddings.
    """
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)  # L2 similarity
    index.add(embeddings)
    return index

def search_faiss_index(index, query_embedding, top_k=5):
    """
    Searches the FAISS index and returns the top-k closest matches.
    """
    distances, indices = index.search(query_embedding, top_k)
    return indices, distances

def save_faiss_index(index, file_path):
    """
    Saves the FAISS index to a file.
    """
    faiss.write_index(index, file_path)

def load_faiss_index(file_path):
    """
    Loads the FAISS index from a file.
    """
    return faiss.read_index(file_path)

# Step 3: Custom Query and Chat Streaming
async def custom_query_with_groq(query, retrieved_chunks, model="llama-3.3-70b-versatile"):
    """
    Asynchronous function to interact with the Grok API for chat streaming.
    """
    client = AsyncGroq(api_key="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")

    # Prepare the conversation context with retrieved chunks
    context = "\n".join(retrieved_chunks) if retrieved_chunks else "The knowledge base does not contain sufficient information for this query."
    system_message = (
    "You are an intelligent assistant. Use the provided context to answer the user's question. "
    "If the context is insufficient, provide an accurate response based on your own knowledge. "
    "Then, at the end of your answer, include a section labeled 'Follow-up questions:' "
    "with one to three potential follow-up questions."
)

    stream = await client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Context:\n{context}\n\nQuery:\n{query}"}
        ],
        model="llama3-70b-8192",
        temperature=0.5,
        top_p=1,
        stream=True,
    )
    response = ""
    followups = []

    # Stream the response and separate follow-ups
    async for chunk in stream:
        delta_content = chunk.choices[0].delta.content
        if delta_content:  # Ensure delta_content is not None
            response += delta_content
            print(delta_content, end="")

    # Extract follow-ups from the response (assumes Grok model includes them clearly in the response)
    if "Follow-up questions:" in response:
        followups_section = response.split("Follow-up questions:")[-1].strip()
        followups = followups_section.split("\n")[:3]

    return response, followups

# Main Function
async def main():
    # Load embedding model
    embedding_model = SentenceTransformer("all-mpnet-base-v2")  # Updated for better embeddings

    # Directory containing PDF files
    pdf_dir = "./document"  # Replace with your directory path

    # Process PDFs
    all_chunks = []
    for filename in os.listdir(pdf_dir):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, filename)
            chunks = process_pdf(pdf_path)
            all_chunks.extend(chunks)

    # Generate embeddings
    embeddings = generate_embeddings(all_chunks, embedding_model)

    # Create FAISS index
    index_file_path = "index_file.faiss"
    if os.path.exists(index_file_path):
        index = load_faiss_index(index_file_path)
    else:
        index = create_faiss_index(embeddings)
        save_faiss_index(index, index_file_path)

    # Input custom query
    user_query = input("Enter your query: ")

    # Generate embedding for query
    query_embedding = embedding_model.encode([user_query])

    # Search FAISS index
    indices, distances = search_faiss_index(index, query_embedding)

    # Set a threshold for relevance; use LLM's knowledge if no good matches are found
    relevance_threshold = 0.5  # Adjust based on experimentation
    if distances[0][0] > relevance_threshold:  # High distance implies low relevance
        print("Insufficient context. Using LLM's knowledge base...")
        top_chunks = []
    else:
        top_chunks = [all_chunks[i] for i in indices[0]]

    # Use Grok API for answering and follow-ups
    print("\nResponse:")
    response, followups = await custom_query_with_groq(user_query, top_chunks)

    # Print follow-up questions
    if followups:
        print("\nFollow-up questions:")
        for followup in followups:
            print(followup)

if __name__ == "__main__":
    asyncio.run(main())