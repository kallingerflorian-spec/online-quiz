import os
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pathlib import Path

app = FastAPI()

# Die 3 festen Fragen
QUESTIONS = [
    {
        "id": 1,
        "type": "sort", # Reihenfolgeaufgabe (Millionenshow)
        "question": "Ordne diese Berge nach ihrer Höhe (Niedrigst nach Höchst):",
        "options": {"A": "Großglockner", "B": "Mont Blanc", "C": "Zugspitze", "D": "Mount Everest"},
        "correct": "CABD" # Zugspitze (2962m), Großglockner (3798m), Mont Blanc (4807m), Mount Everest (8848m)
    },
    {
        "id": 2,
        "type": "choice",
        "question": "Welche Farbe hat eine reife Banane?",
        "options": {"A": "Blau", "B": "Gelb", "C": "Rot", "D": "Grün"},
        "correct": "B"
    },
    {
        "id": 3,
        "type": "choice",
        "question": "In welchem Jahr befinden wir sich jetzt?",
        "options": {"A": "2020", "B": "2024", "C": "2026", "D": "2030"},
        "correct": "C"
    }
]

class GameManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.scores: dict[str, float] = {} # Name: Punkte
        self.current_question_idx = -1
        self.question_start_time = 0.0

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = GameManager()

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
            
            if data.get("type") == "answer":
                now = time.time()
                elapsed = now - manager.question_start_time # Zeit in Sekunden
                
                player = data.get("player")
                answer = data.get("answer")
                
                current_q = QUESTIONS[manager.current_question_idx]
                is_correct = answer == current_q["correct"]
                
                if is_correct:
                    if current_q["type"] == "sort":
                        # Je schneller, desto mehr Bonuspunkte (Max 1000, Abzug pro Sekunde)
                        bonus = max(0, int((20 - elapsed) * 50)) 
                        points = 500 + bonus
                    else:
                        points = 1000
                    manager.scores[player] = manager.scores.get(player, 0) + points
                
                await manager.broadcast({"type": "scores", "data": manager.scores})
                
            elif data.get("type") == "next_question":
                manager.current_question_idx += 1
                if manager.current_question_idx < len(QUESTIONS):
                    manager.question_start_time = time.time()
                    q = QUESTIONS[manager.current_question_idx]
                    await manager.broadcast({"type": "question", "data": q})
                else:
                    await manager.broadcast({"type": "game_over", "data": manager.scores})
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
