from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/", include_in_schema=False)
async def index():
    return FileResponse("./static/index.html", media_type="text/html")

