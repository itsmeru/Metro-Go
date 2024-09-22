import asyncio
import json
import os
import sys
import websockets
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.db_set import get_redis_connection

redis = get_redis_connection()

connected = set()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def redis_listener():
    pubsub = redis.pubsub()
    pubsub.subscribe("updates_channel")
    logger.info("Redis listener started")
    
    while True:
        message = await asyncio.get_event_loop().run_in_executor(None, pubsub.get_message, {"timeout": 1.0})
        if message and message['type'] == 'message':
            logger.info(f"Received message from Redis: {message}")
            
            try:
                string_data = json.loads(message["data"])
                data_type = string_data["type"]
                data = await asyncio.get_event_loop().run_in_executor(None, redis.get, f"{data_type}_data")
                if data:
                    data = data.decode("utf-8")
                    await broadcast(json.dumps({
                        "type": data_type,
                        "data": json.loads(data)
                    }))
                else:
                    logger.warning(f"No data found in Redis for type: {string_data['type']}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON: {message['data']}")
            except Exception as e:
                logger.error(f"Error in redis_listener: {e}", exc_info=True)
        await asyncio.sleep(0.1)  

async def broadcast(message):
    if connected:
        logger.info(f"Broadcasting to {len(connected)} clients")
        closed = set()
        for ws in connected:
            if not ws.closed:
                try:
                    await ws.send(message)
                except websockets.exceptions.WebSocketException:
                    closed.add(ws)
            else:
                closed.add(ws)
        connected.difference_update(closed)
        if closed:
            logger.info(f"Removed {len(closed)} closed connections")
    else:
        logger.info("No connected clients to broadcast to")

async def handle_websocket(websocket, path):
    client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    logger.info(f"New WebSocket connection: {client_info}")
    connected.add(websocket)
    logger.info(f"Total connections: {len(connected)}")
    try:
        for data_type in ['bike', 'station', 'bus']:
            cached_data = await asyncio.get_event_loop().run_in_executor(None, redis.get, f"{data_type}_data")
            if cached_data:
                cached_data = cached_data.decode('utf-8')
                logger.info(f"Sending {data_type} data to new client")
                await websocket.send(json.dumps({
                    "type": data_type,
                    "data": json.loads(cached_data)
                }))
            else:
                logger.warning(f"No cached data for {data_type}")
        
        logger.info(f"Waiting for messages from client {client_info}")
        async for message in websocket:
            logger.info(f"Received message from client {client_info}: {message}")
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Connection closed for {client_info}")
    except Exception as e:
        logger.error(f"Error in handle_websocket for {client_info}: {e}", exc_info=True)
    finally:
        connected.remove(websocket)
        logger.info(f"Connection removed. Total connections: {len(connected)}")

async def main():
    server = await websockets.serve(
        handle_websocket, 
        "0.0.0.0", 
        8765
    )
    logger.info("WebSocket server started on wss://0.0.0.0:8765")
    await asyncio.gather(server.wait_closed(), redis_listener())

if __name__ == "__main__":
    logger.info("Starting WebSocket server...")
    asyncio.run(main())