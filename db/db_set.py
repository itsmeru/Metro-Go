import redis
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from redis import ConnectionPool

import os
import logging

from dotenv import load_dotenv
load_dotenv(os.getenv('RDS_METRO'))
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
# DATABASE_URL = f"mysql+aiomysql://{os.getenv('RDS_USER')}:{os.getenv('RDS_PASSWORD')}@{os.getenv('RDS_HOST')}:{os.getenv('RDS_PORT')}/{os.getenv('RDS_METRO')}"
# DATABASE_URL = f"mysql+aiomysql://{os.getenv('RDS_USER')}:{os.getenv('RDS_PASSWORD')}@127.0.0.1:3307/metro"

DATABASE_URL = f"mysql+aiomysql://root:betty520@mydb:3306/metro"



engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False,
    future=True
)

async_session = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False
)
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


# 創建 Redis 連接池
redis_pool = ConnectionPool(host="redis", port=6379, db=1, max_connections=10)

def get_redis_connection():
    return redis.Redis(connection_pool=redis_pool)

__all__ = ['engine', 'async_session', 'get_db']