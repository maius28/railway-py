# 后果影响预估的参数和返回值

from pydantic import BaseModel, Field
from typing import Dict, List, Union, Optional, Any
from enum import IntEnum, Enum
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


# 图的类
# 节点类型枚举
class NodeType(str, Enum):
    ACTION = "action"
    WARN = "warn"
    BRANCH_SELECTION = "branch_selection"

# 节点状态枚举
class NodeState(str, Enum):
    NOT_DONE = "not done"
    DONE = "done"

# 节点参数类
class NodeArg(BaseModel):
    time: Optional[str] = None
    locate: Optional[str] = None

# 图节点类
class GraphNode(BaseModel):
    description: str
    type: str  # 使用字符串以支持自定义类型
    predict_time: str
    state: str = "not done"
    next: Optional[Union[str, List[str]]] = None
    options: Optional[Dict[str, str]] = None  # 用于分支选择
    arg: Optional[List[NodeArg]] = None  # 可选参数列表

# 事件图结构
class EventGraph(BaseModel):
    __root__: Dict[str, GraphNode]

class PredictRequest(BaseModel):
    args: EventArgs
    graph: Dict[str, GraphNode]

    
