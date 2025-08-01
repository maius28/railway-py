from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.error_handler import register_exception_handlers
from app.api.router import api_router
from app.core.database import db_connection
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Railway Python API", version="1.0.0")

register_exception_handlers(app)

app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("正在启动 Railway Python API...")
    
    # 初始化数据库连接
    try:
        if db_connection.connect():
            logger.info("数据库连接初始化成功")
        else:
            logger.error("数据库连接初始化失败")
    except Exception as e:
        logger.error(f"数据库连接初始化异常: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    logger.info("正在关闭 Railway Python API...")
    
    # 关闭数据库连接
    try:
        db_connection.close()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {e}")

@app.get("/ping")
def ping():
    return {"code": 200, "msg": "pong", "data": None} 