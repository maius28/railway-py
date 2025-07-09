from fastapi import APIRouter
from pydantic import BaseModel
from app.services import algorithm
from app.models.response import ResponseModel

router = APIRouter()

class AddRequest(BaseModel):
    a:float
    b:float


@router.post("/add", response_model=ResponseModel)
def add_numbers(request: AddRequest):
    result = algorithm.add(request.a, request.b)
    return ResponseModel.success(result)
