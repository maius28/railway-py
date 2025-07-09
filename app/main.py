from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.error_handler import register_exception_handlers
from app.api.router import api_router

app = FastAPI(title="Railway Python API", version="1.0.0")

register_exception_handlers(app)

app.include_router(api_router, prefix="/api")

@app.get("/ping")
def ping():
    return {"code": 200, "msg": "pong", "data": None} 