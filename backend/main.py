from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
from rag import custom_query_with_groq, load_faiss_index, search_faiss_index, SentenceTransformer

app = FastAPI()

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
index = load_faiss_index(index_file_path)
embedding_model = SentenceTransformer("all-mpnet-base-v2")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            response, followups = await handle_query(data)
            await manager.send_personal_message(response, websocket)
            if followups:
                followup_message = "\n".join(followups)
                await manager.send_personal_message(f"Follow-up questions:\n{followup_message}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("A client disconnected")

async def handle_query(query: str):
    query_embedding = embedding_model.encode([query])
    indices, distances = search_faiss_index(index, query_embedding)
    relevance_threshold = 0.5
    if distances[0][0] > relevance_threshold:
        top_chunks = []
    else:
        top_chunks = [all_chunks[i] for i in indices[0]]
    response, followups = await custom_query_with_groq(query, top_chunks)
    return response, followups