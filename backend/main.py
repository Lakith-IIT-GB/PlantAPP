import os
import asyncio
import logging
import faiss
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Tuple
from analyze_plant_image import analyze_plant_image
from updated_rag_without_sentence_transfromers import custom_query_with_groq, load_faiss_index, load_text_chunks

# Initialize FastAPI app
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://plant-app-flxr.vercel.app/"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.conversation_history: Dict[WebSocket, List[Dict[str, str]]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.conversation_history[websocket] = []

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if websocket in self.conversation_history:
            del self.conversation_history[websocket]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    def add_to_history(self, websocket: WebSocket, role: str, content: str):
        if websocket not in self.conversation_history:
            self.conversation_history[websocket] = []
        self.conversation_history[websocket].append({
            "role": role,
            "content": content
        })

    def get_history(self, websocket: WebSocket) -> List[Dict[str, str]]:
        return self.conversation_history.get(websocket, [])
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Load FAISS index and text chunks at startup
index_file_path = "index_file.faiss"
chunks_file_path = "text_chunks.txt"
query_embedding_path = "query_embedding.npy"

try:
    index = load_faiss_index(index_file_path)
    all_chunks = load_text_chunks(chunks_file_path)
except Exception as e:
    logger.error(f"Failed to load FAISS index or text chunks: {e}")
    raise

async def handle_query(query: str, history: List[Dict[str, str]] = None) -> Tuple[str, List[str]]:
    try:
        # Load all precomputed embeddings
        embeddings = np.load("precomputed_embeddings.npy")
        
        # Get index for first embedding only
        first_embedding = embeddings[0].reshape(1, -1)
        indices, distances = index.search(first_embedding, 5)
        
        # Select relevant chunks
        relevance_threshold = 0.5
        top_chunks = []
        if distances[0][0] <= relevance_threshold:
            # Convert float indices to integers
            indices_int = indices[0].astype(int)
            top_chunks = [all_chunks[i] for i in indices_int if i < len(all_chunks)]
        
        response, followups = await custom_query_with_groq(query, top_chunks, history)
        return response, followups
        
    except Exception as e:
        logger.error(f"Error handling query: {str(e)}")
        logger.exception("Full traceback:")
        return "An error occurred while processing your query.", []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            manager.add_to_history(websocket, "user", data)
            
            history = manager.get_history(websocket)
            response, followups = await handle_query(data, history)
            
            manager.add_to_history(websocket, "assistant", response)
            
            if followups:
                combined_response = f"{response}\n\nFollow-up questions:\n" + "\n".join([f"- {q}" for q in followups])
            else:
                combined_response = response
                
            await manager.send_personal_message(combined_response, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logging.info("Client disconnected")

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        analysis_result = await analyze_plant_image(image_bytes)
        return {"analysis": analysis_result}
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)