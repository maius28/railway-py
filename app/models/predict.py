# 后果影响预估的参数和返回值

from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import IntEnum
from datetime import datetime


class EventType(IntEnum):
    """事件类型枚举"""
    SEVERE_WEATHER = 1    # 恶劣天气
    EQUIPMENT_FAILURE = 2  # 设备故障
    HUMAN_FACTOR = 3      # 人为因素
    SPECIAL_ENVIRONMENT = 4  # 特殊环境

class UpDownType(IntEnum):
    """上下行类型枚举"""
    UP = 1  # 上行
    DOWN = 2  # 下行

class EventArgs(BaseModel):
    eventId: int
    eventName: str
    startTime: datetime = Field(..., description="Format: YYYY-MM-DD HH:MM:SS")
    trainNo: str
    preStation: str
    nextStation: str
    upDown: UpDownType
    addressType: str
    eventType: EventType

class PredictRequest(BaseModel):
    args: EventArgs
    
