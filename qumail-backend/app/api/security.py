from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/security", tags=["security"])

@router.get("/status")
async def security_status():
    return {"status": "ok"}
