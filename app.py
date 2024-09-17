from fastapi import *
from fastapi.staticfiles import StaticFiles
from controller import get_mrt_name, get_parking, get_plan, get_ticket,get_time
from view import staticPage
from fastapi.middleware.cors import CORSMiddleware
from db.db_set import engine, get_redis_connection,redis_pool
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MRT API")
app.mount("/static", StaticFiles(directory="static"), name="static")
origins = [
    "https://ruru888.com",
    "http://localhost:8000", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    max_age=600,  # 預檢請求的最大緩存時間（秒）
)

@app.middleware("http")
async def redis_connection(request: Request, call_next):
    request.state.redis = get_redis_connection()
    response = await call_next(request)
    return response

@app.on_event("startup")
async def startup_event():
    logger.info("Application is starting up. Redis pool is ready.")

@app.on_event("shutdown")
async def shutdown_event():
    await engine.dispose()
    logger.info("Application is shutting down. Closing Redis connection pool.")
    if redis_pool:
        try:
            redis_pool.disconnect()
            logger.info("Redis connection pool closed successfully.")
        except Exception as e:
            logger.error(f"Error closing Redis connection pool: {e}")
    else:
        logger.warning("Redis connection pool was not initialized.")
        


app.include_router(get_mrt_name.router)
app.include_router(get_ticket.router)
app.include_router(get_time.router)
app.include_router(get_parking.router)
app.include_router(get_plan.router)
app.include_router(staticPage.router)

