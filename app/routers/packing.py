from fastapi import APIRouter
from app.models.request import PackingRequest
from app.models.response import PackingResponse

router = APIRouter()

@router.post("/packing-advice", response_model=PackingResponse)
async def get_packing_advice(request: PackingRequest):
    pass