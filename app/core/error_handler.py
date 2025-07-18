from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from app.core.funcLogger import logger


def json_error_response(code: int, msg: str, data=None):
    return {"code": code, "msg": msg, "data": data}


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # 记录HTTP异常到日志
        logger.error(f"HTTP Exception occurred: {exc.status_code} - {exc.detail} | Request: {request.method} {request.url}")
        return JSONResponse(status_code=exc.status_code, content=json_error_response(exc.status_code, exc.detail))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # 记录验证异常到日志
        logger.error(f"Validation Error occurred: {exc.errors()} | Request: {request.method} {request.url}")
        return JSONResponse(status_code=422, content=json_error_response(422, "数据异常"))

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # 记录详细的异常信息到日志
        error_msg = f"Unexpected exception occurred: {type(exc).__name__}: {str(exc)}"
        logger.error(f"{error_msg} | Request: {request.method} {request.url}")
        logger.error(f"Exception traceback:\n{traceback.format_exc()}")
        
        # 返回统一的错误信息给前端
        return JSONResponse(status_code=500, content=json_error_response(500, "数据异常")) 