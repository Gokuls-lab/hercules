# hercules/backend/app/websocket_manager.py
from fastapi import WebSocket
from typing import Dict, List, DefaultDict
from collections import defaultdict
import json
import datetime

class WebSocketManager:
    def __init__(self):
        # active_connections: room_id -> list of WebSockets
        self.active_connections: DefaultDict[str, List[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        self.active_connections[room_id].append(websocket)
        print(f"WebSocket connected: {websocket.client} for room {room_id}")
        # Optionally, send a welcome message or initial state
        # await self.send_personal_message({"message": "Connected to room " + room_id}, websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if websocket in self.active_connections[room_id]:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]: # If list is empty
                del self.active_connections[room_id] # Clean up empty room_id entry
        print(f"WebSocket disconnected: {websocket.client} from room {room_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Error sending personal message to {websocket.client}: {e}")


    async def broadcast_to_room(self, room_id: str, message: dict):
        # Add a timestamp to all broadcast messages
        message_with_timestamp = message.copy()
        if "timestamp" not in message_with_timestamp:
            message_with_timestamp["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        disconnected_sockets = []
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_text(json.dumps(message_with_timestamp))
                except Exception as e:
                    print(f"Error broadcasting to {connection.client} in room {room_id}: {e}. Marking for disconnect.")
                    # If sending fails, assume the client is disconnected.
                    disconnected_sockets.append(connection)
            
            # Clean up disconnected sockets from this room's list
            for sock in disconnected_sockets:
                self.disconnect(sock, room_id)

# Global instance of the manager
# This simple approach works for a single server instance.
# For multi-server setups, a more robust solution (e.g., Redis Pub/Sub) would be needed.
websocket_manager = WebSocketManager()
