# 后果影响预估的参数和返回值

from pydantic import BaseModel, RootModel, Field
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
class EventGraph(RootModel[Dict[str, GraphNode]]):
    root: Dict[str, GraphNode]

# 时间估算图的点状态
class PointStatus(IntEnum):
    """点状态枚举"""
    PENDING = 0  # 待处理
    PROCESSING = 1  # 处理中
    COMPLETED = 2  # 已完成

# 时间估算图的点
class TimePoint(BaseModel):
    status: PointStatus
    predictTime: int  # 预测时间（分钟）

# 时间估算图
class TimeEstimateGraph(BaseModel):
    mermaidInfo: str = ""
    points: List[Dict[str, TimePoint]]

# 统计信息
class Statistics(BaseModel):
    impactDuration: int  # 影响持续时间
    affectTrainsNum: int  # 受影响列车总数
    highAffectTrainsNum: int  # 高影响列车数
    middleAffectTrainsNum: int  # 中等影响列车数
    lowAffectTrainsNum: int  # 低影响列车数

# 列车状态枚举
class TrainStatus(str, Enum):
    NORMAL = "正常"
    DELAYED = "晚点"
    CANCELLED = "取消"
    REROUTED = "改路"

# 时间单位枚举
class TimeUnit(str, Enum):
    MINUTE = "min"
    HOUR = "h"

# 列车表信息
class TrainTableItem(BaseModel):
    trainNo: str  # 车次
    startStation: str  # 起始站
    endStation: str  # 终点站
    nextStation: str  # 下一站
    status: TrainStatus  # 状态
    affectTime: int  # 影响时间
    timeUnit: TimeUnit  # 时间单位

# 列车站点图（暂时为空结构，可根据需要扩展）
class TrainStationGraph(BaseModel):
    pass

# 预测响应结果
class PredictResponse(BaseModel):
    timeEstimateGraph: TimeEstimateGraph
    statistics: Statistics
    trainTable: List[TrainTableItem]
    trainStationGraph: TrainStationGraph
    
# 预测请求模型
class PredictRequest(BaseModel):
    args: EventArgs
    graph: Dict[str, GraphNode]

    
