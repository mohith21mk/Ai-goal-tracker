import json
from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def disconnect_user(self, user_id: int):
        if user_id in self.active_connections:
            connections = self.active_connections[user_id].copy()
            for connection in connections:
                await connection.close(code=1008, reason="Session revoked")
            if user_id in self.active_connections:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(message)

    async def send_personal_json(self, data: dict, user_id: int):
        if user_id in self.active_connections:
            message = json.dumps(data, default=str)
            for connection in self.active_connections[user_id]:
                await connection.send_text(message)

manager = ConnectionManager()
