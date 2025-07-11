from fastapi import APIRouter
from pydantic import BaseModel
from app.models.predict import PredictRequest
from app.services import algorithm
from app.models.response import ResponseModel
from app.core.funcLogger import log_function
router = APIRouter()

class AddRequest(BaseModel):
    a:float
    b:float


@router.post("/add", response_model=ResponseModel)
@log_function
def add_numbers(request: AddRequest):
    result = algorithm.add(request.a, request.b)
    return ResponseModel.success(data=result)

# 后果预估算法入口
@router.post("/affect/predict", response_model=ResponseModel)
@log_function
def forecast(request: PredictRequest):
    # 这里可以调用后果预估算法的具体实现
    return ResponseModel.success(request)