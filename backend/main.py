from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import asyncio
from rag import custom_query_with_groq, load_faiss_index, search_faiss_index, SentenceTransformer
import logging
import base64
from analyze_plant_image import analyze_plant_image

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # You can restrict this to ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Load the FAISS index and embedding model once at startup
index_file_path = "index_file.faiss"
try:
    index = load_faiss_index(index_file_path)
    all_chunks = [...]  # Load or define your chunks here
    embedding_model = SentenceTransformer("all-mpnet-base-v2")
except Exception as e:
    logger.error(f"Failed to load FAISS index or embedding model: {e}")
    raise

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            response, followups = await handle_query(data)
            await manager.send_personal_message(response, websocket)
            if followups:
                followup_message = "\n".join([f"- {q}" for q in followups])  # Format follow-ups as bullet points
                await manager.send_personal_message(f"Follow-up questions:\n{followup_message}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("A client disconnected")
        await manager.broadcast("A client disconnected")

async def handle_query(query: str):
    try:
        query_embedding = embedding_model.encode([query])
        indices, distances = search_faiss_index(index, query_embedding)
        relevance_threshold = 0.5  # Adjust based on your dataset
        if distances[0][0] > relevance_threshold:
            top_chunks = []
        else:
            top_chunks = [all_chunks[i] for i in indices[0]]
        response, followups = await custom_query_with_groq(query, top_chunks)
        return response, followups
    except Exception as e:
        logger.error(f"Error handling query: {e}")
        return "An error occurred while processing your query.", []
    
@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        analysis_result = await analyze_plant_image(image_bytes)  # Add await here
        
        return {"analysis": analysis_result}
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        return {"error": str(e)}
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)