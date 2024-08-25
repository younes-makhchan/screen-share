import asyncio
import websockets
import json
from typing import Dict, Set

class ScreenShareServer:
    def __init__(self):
        self.master: websockets.WebSocketServerProtocol = None
        self.children: Set[websockets.WebSocketServerProtocol] = set()
        self.current_screen: str = None

    async def handle_connection(self, websocket: websockets.WebSocketServerProtocol, path: str):
        try:
            client_type = await self.authenticate_client(websocket)
            if client_type == "master":
                await self.handle_master(websocket)
            elif client_type == "child":
                await self.handle_child(websocket)
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            if websocket in self.children:
                self.children.remove(websocket)
            if websocket == self.master:
                self.master = None
                self.current_screen = None

    async def authenticate_client(self, websocket: websockets.WebSocketServerProtocol) -> str:
        auth_message = await websocket.recv()
        auth_data = json.loads(auth_message)
        return auth_data.get("client_type")

    async def handle_master(self, websocket: websockets.WebSocketServerProtocol):
        if self.master:
            await websocket.close(1008, "Master already connected")
            return
        
        self.master = websocket
        try:
            async for message in websocket:
                screen_data = json.loads(message)
                self.current_screen = screen_data.get("screen")
                await self.broadcast_screen()
        finally:
            self.master = None
            self.current_screen = None

    async def handle_child(self, websocket: websockets.WebSocketServerProtocol):
        self.children.add(websocket)
        if self.current_screen:
            await self.send_screen(websocket)
        try:
            async for message in websocket:
                # Children don't send messages in this implementation
                pass
        finally:
            self.children.remove(websocket)

    async def broadcast_screen(self):
        if not self.current_screen:
            return
        await asyncio.gather(
            *[self.send_screen(child) for child in self.children],
            return_exceptions=True
        )

    async def send_screen(self, websocket: websockets.WebSocketServerProtocol):
        try:
            await websocket.send(json.dumps({"screen": self.current_screen}))
        except websockets.exceptions.ConnectionClosed:
            self.children.remove(websocket)

async def main():
    server = ScreenShareServer()
    async with websockets.serve(server.handle_connection, "0.0.0.0", 9090):
        print("Server started on ws://0.0.0.0:9090")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())