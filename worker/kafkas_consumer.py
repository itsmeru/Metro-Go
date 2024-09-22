import asyncio
import json
import os
import logging
from dotenv import load_dotenv
from aiokafka import AIOKafkaConsumer
import sys
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
CONSUMER_READY_FILE = "/tmp/kafka_consumer_ready"
kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
bike_topic = "bike_data"
metro_topic = "metro_data"
bus_topic = "bus_data"

redis = get_redis_connection()

# 最後一次接收數據的時間
last_data_time = {}

async def process_and_store_data(data, data_type):
    try:
        current_time = datetime.now()
        if data:
            redis.set(f"{data_type}_data", json.dumps(data))
            redis.publish("updates_channel", json.dumps({"type": data_type, "action": "update"}))
            last_data_time[data_type] = current_time
            logger.info(f"{data_type.capitalize()} data processed and stored in Redis")
        else:
            no_data_message = {
                "no_data": True,
                "last_update": last_data_time.get(data_type, current_time.isoformat()),
                "current_time": current_time.isoformat()
            }
            redis.publish("updates_channel", json.dumps({"type": data_type, "action": "no_data", "data": no_data_message}))
            logger.info(f"No {data_type} data available, published no-data message")
        
        last_data_time[data_type] = current_time
    except Exception as e:
        logger.error(f"Error in process_and_store_{data_type}_data: {e}", exc_info=True)

async def process_and_store_bus_data(bus_data):
    try:
        bus_live_datas = await get_bus(bus_data) if bus_data else {}
        await process_and_store_data(bus_live_datas, "bus")
    except Exception as e:
        logger.error(f"Error in process_and_store_bus_data: {e}", exc_info=True)

async def process_and_store_bike_data(bike_data):
    try:
        bike_results = await get_bike(bike_data) if bike_data else {}
        await process_and_store_data(bike_results, "bike")
    except Exception as e:
        logger.error(f"Error in process_and_store_bike_data: {e}", exc_info=True)

async def process_and_store_metro_data(real_time_datas):
    try:
        station_position_data = await get_metro(real_time_datas) if real_time_datas else {}
        await process_and_store_data(dict(station_position_data), "station")
    except Exception as e:
        logger.error(f"Error in process_and_store_metro_data: {e}", exc_info=True)

async def setup_kafka_consumer(topic, group_id, max_retries=5, retry_interval=5):
    for attempt in range(max_retries):
        try:
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
        except Exception as e:
            logger.error(f"Failed to connect to Kafka for topic {topic}, attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_interval)
            else:
                raise

async def kafka_consumer(consumer, topic, process_func):
    try:
        if topic == "bike_data":
            bike_data = {}
            async for message in consumer:
                items = message.value
                if items == "end_marker":
                    await process_func(bike_data)
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
    results = await asyncio.gather(*setup_tasks, return_exceptions=True)
    for topic, result in zip(topics, results):
        if isinstance(result, Exception):
            logger.error(f"Failed to set up consumer for topic {topic}: {result}")
        else:
            consumers[topic] = result
    return consumers

async def check_data_freshness():
    while True:
        current_time = datetime.now()
        for data_type in ['bike', 'station', 'bus']:
            last_time = last_data_time.get(data_type)
            if not last_time or (current_time - last_time) > timedelta(minutes=10):
                logger.warning(f"No fresh {data_type} data for more than 10 minutes or no data received yet")
                await process_and_store_data(None, data_type)
        await asyncio.sleep(60)  # 每分鐘檢查一次

async def main():
    consumers = {}
    topics = [bike_topic, metro_topic, bus_topic]
    group_id = "data_consumer_group"
    try:
        consumers = await setup_kafka_consumers(topics, group_id)
        with open(CONSUMER_READY_FILE, 'w') as f:
                    f.write('ready')
        logger.info(f"Created consumer ready file: {CONSUMER_READY_FILE}")
        consumer_tasks = [
            kafka_consumer(consumers[bike_topic], bike_topic, process_and_store_bike_data),
            kafka_consumer(consumers[metro_topic], metro_topic, process_and_store_metro_data),
            kafka_consumer(consumers[bus_topic], bus_topic, process_and_store_bus_data)
        ]

        await asyncio.gather(*consumer_tasks, check_data_freshness())
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
    finally:
        if os.path.exists(CONSUMER_READY_FILE):
            os.remove(CONSUMER_READY_FILE)
            logger.info(f"Removed consumer ready file: {CONSUMER_READY_FILE}")
        for consumer in consumers.values():
            await consumer.stop()

if __name__ == "__main__":
    asyncio.run(main())