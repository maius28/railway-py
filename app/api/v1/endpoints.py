from fastapi import APIRouter,Request,Body
from app.models.predict import PredictRequest
from app.services import algorithm
from app.models.response import ResponseModel
from app.core.funcLogger import log_function

router = APIRouter()

# # 后果预估算法入口（统一入口，支持后果预估和晚点预测）
# @router.post("/affect/predict", response_model=ResponseModel)
# @log_function
# def forecast(request):
#     # 这里可以调用后果预估算法的具体实现
#     algorithm_result = algorithm.get_predict_result(request)
#     return ResponseModel.success(algorithm_result)



@router.post("/affect/predict", response_model=ResponseModel)
@log_function
def forecast(request: dict = Body(...)):
    algorithm_result = algorithm.get_predict_result(request)
    return ResponseModel.success(algorithm_result)