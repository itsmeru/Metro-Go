from fastapi import *
from fastapi.staticfiles import StaticFiles
from controller import getMrtName,getTicket,getTime,getParking,getPlan
from view import staticPage
from db.db_set import engine, get_redis_connection,redis_pool
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


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
        


app.include_router(getMrtName.router)
app.include_router(staticPage.router)
app.include_router(getTicket.router)
app.include_router(getTime.router)
app.include_router(getParking.router)
app.include_router(getPlan.router)

