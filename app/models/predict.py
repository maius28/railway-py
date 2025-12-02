# 后果影响预估的参数和返回值

from pydantic import BaseModel, Field
from typing import List, Union, Optional
from enum import IntEnum, Enum
from datetime import datetime

class EventType(IntEnum):
    """事件类型枚举"""
    # SEVERE_WEATHER = 1    # 恶劣天气
    # EQUIPMENT_FAILURE = 2  # 设备故障
    # HUMAN_FACTOR = 3      # 人为因素
    # SPECIAL_ENVIRONMENT = 4  # 特殊环境
    
    EQUIPMENT_FAILURE = 0  # 设备故障
    HUMAN_FACTOR = 1      # 人为因素
    SEVERE_WEATHER = 2    # 恶劣天气
    SPECIAL_ENVIRONMENT = 3  # 地质灾害

class EventLocationType(IntEnum):
    STATION = 0 #车站
    SECTION = 1 #区间

class UpDownType(int, Enum):
    """上下行类型枚举"""
    UP = 0  # 上行
    DOWN = 1  # 下行

class HarshEnvType(int, Enum):
    """泥石流类型"""
    STICK = 0 #黏性泥石流
    THIN = 1 #稀性

class LandSlideType(int, Enum):
    """滑坡类型"""
    SURFACE = 0 #表层滑坡
    DEEP = 1 #深层

class ObstacleType(int, Enum):
    """障碍物类型"""
    NO = 0 #无
    STONE = 1 #石头
    WOOD = 2 #积木

class ImpactConsequenceType(int, Enum):
    """预计影响后果"""
    NO = 0 #无
    SLOWDOWN = 1 #降速
    INTERRUPT = 2 #中断

class EventArgs(BaseModel):
    event_id: int
    event_name: str
    start_time: datetime = Field(..., description="Format: YYYY-MM-DD HH:MM:SS")
    train_no: str
    pre_station: str
    next_station: str
    up_down: UpDownType
    address_type: str
    event_type: EventType
    wind_speed: Optional[float] = None  # 风速
    snow_depth: Optional[float] = None  # 降雪量
    rainfall: Optional[float] = None  # 降雨量
    visibility: Optional[int] = None  # 能见度
    device_failure_type: Optional[int] = None  # 设备故障类型
    recover_after_disposal: Optional[bool] = None  # 处置后是否恢复
    human_factors_type: Optional[int] = None  # 人为因素事件类型
    collision: Optional[bool] = None  # 是否发生碰撞
    harsh_env_type: Optional[int] = None  # 泥石流类型
    catenary_hang: Optional[bool] = None  # 接触网是否挂异物
    catenary_size: Optional[float] = None  # 异物大小

class Args(BaseModel):
    event_type: EventType #事件类型
    event_id: str #事件名称
    event_time: datetime = Field(..., description="Format: YYYY-MM-DD HH:MM:SS") #发生时间
    event_location: EventLocationType #事件位置
    event_location_value: str #事件位置的值
    direction: UpDownType #行别
    train_id: Optional[str] #影响首次列车号
    address: str #里程位置
    incidence: Optional[str] #影响范围
    second_accident: Optional[bool] #是否有二次事故
    impact_time: Optional[int] = None #预计影响分钟数
    wind_speed: Optional[float] = None  # 风速
    snowfall: Optional[float] = None  # 降雪量
    rainfall: Optional[float] = None  # 降雨量
    catenary_frozen: Optional[bool] = None #接触网是否结冰
    recover_after_disposal: Optional[bool] = None  # 处置后是否恢复
    collision: Optional[bool] = None  # 是否发生碰撞
    harsh_env_type: Optional[HarshEnvType] = None  # 泥石流类型
    landslide_type: Optional[LandSlideType] = None #滑坡类型
    carriage_number: Optional[str] = None #所在车厢号
    warter_depth: Optional[float] = None #积水深度
    snow_depth: Optional[float] = None #积雪厚度
    obstacle:Optional[ObstacleType] = None #障碍物
    foreign_obj_type: Optional[str] = None  # 异物名称
    foreign_obj_size: Optional[float] = None  # 异物大小
    impact_consequence: Optional[ImpactConsequenceType] = None #预计影响后果
    detail: Optional[str] = None #详细描述



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
    statistics: Statistics  # 统计信息
    train_table: List[TrainTableItem]  # 列车表
    affect_graph: AffectGraph  # 影响图
    
# 预测请求模型
class PredictRequest(BaseModel):
    args: Args


class TrainDelayRequest(BaseModel):
    time_gap: List[float]
    dist: float
    lats: List[float]
    lngs: List[float]
    driverID: Union[int, str]
    weekID: Union[int, str]
    states: List[float]
    timeID: int
    time: float
    dateID: Union[int, str]
    dist_gap: List[float]
    weather: List[Union[int, float, str]]
    temperature: List[Union[int, float, str]]
    wind: List[Union[int, float, str]]

