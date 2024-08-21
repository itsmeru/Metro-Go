from fastapi import *
from fastapi.staticfiles import StaticFiles
from controller import getMrtName,getTicket,getTime,getParking
from view import staticPage
from db.db_set import get_redis_connection,redis_pool
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")



@app.middleware("http")
async def redis_connection(request: Request, call_next):
    request.state.redis = get_redis_connection()
    response = await call_next(request)
    return response

@app.on_event("shutdown")
async def shutdown_event():
    # 在應用關閉時關閉 Redis 連接池
    await redis_pool.disconnect()

app.include_router(getMrtName.router)
app.include_router(staticPage.router)
app.include_router(getTicket.router)
app.include_router(getTime.router)
app.include_router(getParking.router)

