import asyncio
import json
import os
import logging
from dotenv import load_dotenv
from aiokafka import AIOKafkaConsumer
import websockets
import sys
import os
from datetime import datetime, timedelta

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 將父目錄添加到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.db_set import get_redis_connection
from getBike import get_bike
from getMetro import get_metro
from getBus import get_bus

load_dotenv()

kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
bike_topic = "bike_data"
metro_topic = "metro_data"
bus_topic = "bus_data"

connected = set()
redis = get_redis_connection()

# 新增：用於跟踪最後一次接收數據的時間
last_data_time = {}

async def process_and_send_data(data, data_type):
    try:
        if data:
            redis.set(f"{data_type}_data", json.dumps(data))
            await send_to_websockets(data, data_type)
            last_data_time[data_type] = datetime.now()
            logger.info(f"{data_type.capitalize()} data cached and sent successfully")
        else:
            # 如果沒有數據，發送一個特殊的消息
            no_data_message = {"no_data": True, "last_update": last_data_time.get(data_type, "Unknown")}
            await send_to_websockets(no_data_message, data_type)
            logger.info(f"No {data_type} data available, sent no-data message")
    except Exception as e:
        logger.error(f"Error in process_and_send_{data_type}_data: {e}", exc_info=True)

async def load_json_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Error loading file {filename}: {e}")
        return None

async def process_and_send_bus_data(bus_data):
    try:
        bus_live_datas = await get_bus(bus_data) if bus_data else {}
        await process_and_send_data(bus_live_datas, "bus")
    except Exception as e:
        logger.error(f"Error in process_and_send_bus_data: {e}", exc_info=True)

async def process_and_send_bike_data(bike_data):
    try:
        bike_results = await get_bike(bike_data) if bike_data else {}
        await process_and_send_data(bike_results, "bike")
    except Exception as e:
        logger.error(f"Error in process_and_send_bike_data: {e}", exc_info=True)

async def process_and_send_metro_data(real_time_datas):
    try:
        station_position_data = await get_metro(real_time_datas) if real_time_datas else {}
        await process_and_send_data(dict(station_position_data), "station")
    except Exception as e:
        logger.error(f"Error in process_and_send_metro_data: {e}", exc_info=True)

async def send_to_websockets(data_to_send, data_type):
    message = {
        "type": data_type,
        "data": data_to_send
    }
    message_json = json.dumps(message, ensure_ascii=False)
    if connected:
        await asyncio.gather(*[ws.send(message_json) for ws in connected if not ws.closed])

async def handle_websocket(websocket):
    connected.add(websocket)
    try:
        # 當新的 WebSocket 連接建立時，發送 Redis 中的緩存數據
        for data_type in ['bike', 'station', 'bus']:
            cached_data = redis.get(f"{data_type}_data")
            if cached_data:
                await websocket.send(json.dumps({
                    "type": data_type,
                    "data": json.loads(cached_data)
                }))
        
        await websocket.wait_closed()
    finally:
        connected.remove(websocket)

async def setup_kafka_consumer(topic, group_id, max_retries=5, retry_interval=5):
    for attempt in range(max_retries):
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=kafka_bootstrap_servers,
            group_id=group_id,
            auto_offset_reset="latest",
            enable_auto_commit=True,
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
            session_timeout_ms=10000,
            heartbeat_interval_ms=3000,
            max_poll_interval_ms=20000,
            request_timeout_ms=15000,
            max_partition_fetch_bytes=1048576,
            fetch_max_wait_ms=500,
            connections_max_idle_ms=60000
        )
        
        await consumer.start()
        logger.info(f"Successfully connected to Kafka for topic {topic} after {attempt + 1} attempts")
        return consumer

async def kafka_consumer(consumer, topic, process_func):
    try:
        if topic == "bike_data":
            bike_data = {}
            async for message in consumer:
                items = message.value
                if items == "end_marker":
                    await process_and_send_bike_data(bike_data)
                    bike_data = {}
                else:
                    for item in items:
                        bike_data[item["sno"]] = item
        else:
            data_buffer = []
            async for message in consumer:
                if message.value == "end_marker":
                    await process_func(data_buffer)
                    data_buffer = []
                else:
                    data_buffer.append(message.value)
    except Exception as e:
        logger.error(f"Error in {topic}_kafka_consumer: {e}", exc_info=True)

async def setup_kafka_consumers(topics, group_id):
    consumers = {}
    setup_tasks = [setup_kafka_consumer(topic, group_id) for topic in topics]
    results = await asyncio.gather(*setup_tasks)
    for topic, consumer in zip(topics, results):
        consumers[topic] = consumer
    return consumers


async def check_data_freshness():
    while True:
        current_time = datetime.now()
        for data_type in ['bike', 'station', 'bus']:
            last_time = last_data_time.get(data_type)
            if last_time and (current_time - last_time) > timedelta(minutes=10):
                logger.warning(f"No fresh {data_type} data for more than 10 minutes")
                await process_and_send_data(None, data_type)
        await asyncio.sleep(60)  # 每分鐘檢查一次

async def main():
    consumers = {}
    websocket_server = websockets.serve(handle_websocket, "0.0.0.0", 8765)
    topics = [bike_topic, metro_topic, bus_topic]
    group_id = "data_consumer_group"
    try:
        consumers = await setup_kafka_consumers(topics, group_id)

        consumer_tasks = [
            kafka_consumer(consumers[bike_topic], bike_topic, process_and_send_bike_data),
            kafka_consumer(consumers[metro_topic], metro_topic, process_and_send_metro_data),
            kafka_consumer(consumers[bus_topic], bus_topic, process_and_send_bus_data)
        ]

        await asyncio.gather(
            websocket_server,
            *consumer_tasks,
            check_data_freshness()
        )
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        if os.path.exists("/tmp/kafka_consumer_ready"):
            os.remove("/tmp/kafka_consumer_ready")
        for consumer in consumers.values():
            await consumer.stop()

if __name__ == "__main__":
    asyncio.run(main())