import asyncio
import websockets
import json

clients = set()

async def handler(websocket, path):
    clients.add(websocket)
    try:
        async for message in websocket:
            # Broadcast the message to all clients except the sender
            await asyncio.wait([client.send(message) for client in clients if client != websocket])
    finally:
        clients.remove(websocket)

async def main():
    async with websockets.serve(handler, "localhost", 9090):
        print("Server started on ws://localhost:9090")
        await asyncio.Future()  # run forever

asyncio.run(main())