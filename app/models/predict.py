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

# 事件图节点状态
class EventNodeStatus(IntEnum):
    """事件节点状态枚举"""
    PENDING = 0  # 待处理
    PROCESSING = 1  # 处理中
    COMPLETED = 2  # 已完成

# 事件图节点
class EventGraphNode(BaseModel):
    description: str
    predict_time: str  # 预测时间
    real_time: Optional[str] = None  # 实际时间
    status: EventNodeStatus

# 统计信息
class Statistics(BaseModel):
    impact_duration: int  # 影响持续时间
    affect_trains_num: int  # 受影响列车总数
    high_affect_trains_num: int  # 高影响列车数
    middle_affect_trains_num: int  # 中等影响列车数
    low_affect_trains_num: int  # 低影响列车数

# 列车状态枚举
class TrainStatus(IntEnum):
    NORMAL = 0
    DELAYED = 1
    CANCELLED = 2
    REROUTED = 3

# 列车表信息
class TrainTableItem(BaseModel):
    train_id: str  # 车次
    start_station: str  # 起始站
    end_station: str  # 终点站
    next_station: str  # 下一站
    status: TrainStatus  # 状态
    affect_time: int  # 影响时间

# 影响图地址信息
class AffectAddress(BaseModel):
    pointA: str
    pointB: str

# 影响图站点
class AffectPoint(BaseModel):
    id: str
    name: str
    trains: List[str] = []  # 暂时用字符串列表，可根据需要调整

# 列车方向枚举
class TrainDirection(str, Enum):
    UP = "up"
    DOWN = "down"

# 线路上的列车信息
class LineTrainInfo(BaseModel):
    id: str  # 列车ID
    delay: str  # 延误时间
    derection: TrainDirection  # 方向（注意：保持原数据中的拼写"derection"）

# 线路段信息
class LineSegment(BaseModel):
    pointA: str  # 起始站点
    pointB: str  # 终止站点
    trains: List[LineTrainInfo] = []  # 该线路段的列车信息

# 影响图
class AffectGraph(BaseModel):
    address: AffectAddress  # 地址信息
    points: List[AffectPoint]  # 站点列表
    lines: List[List[LineSegment]]  # 线路信息，二维数组

# 预测响应结果
class PredictResponse(BaseModel):
    event_graph: Dict[str, EventGraphNode]  # 事件图
    statistics: Statistics  # 统计信息
    train_table: List[TrainTableItem]  # 列车表
    affect_graph: AffectGraph  # 影响图
    
# 预测请求模型
class PredictRequest(BaseModel):
    args: EventArgs
    graph: Dict[str, GraphNode]

    
