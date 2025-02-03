from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Tuple
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

async def handle_query(query: str, history: List[Dict[str, str]] = None) -> Tuple[str, List[str]]:
    try:
        if history is None:
            history = []
            
        query_embedding = embedding_model.encode([query])
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