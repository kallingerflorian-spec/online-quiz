import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()

# Speicher für aktive Websocket-Verbindungen und Punktestände
class GameManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.scores: dict[str, int] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = GameManager()

# HTML-Hilfsfunktion zum Laden der Frontends
def get_html(file_name: str) -> str:
    return Path(f"templates/{file_name}").read_text()

@app.get("/")
def get_player_page():
    return HTMLResponse(get_html("player.html"))

@app.get("/host")
def get_host_page():
    return HTMLResponse(get_html("host.html"))

@app.websocket("/ws/{client_type}")
async def websocket_endpoint(websocket: WebSocket, client_type: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Wenn ein Spieler antwortet
            if data.get("type") == "answer":
                player = data.get("player")
                is_correct = data.get("correct")
                if is_correct:
                    manager.scores[player] = manager.scores.get(player, 0) + 100
                
                # Punktestand an alle (besonders den Host) senden
                await manager.broadcast({"type": "scores", "data": manager.scores})
                
            # Wenn der Host eine neue Frage sendet
            elif data.get("type") == "next_question":
                await manager.broadcast({"type": "question", "data": data.get("question")})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
