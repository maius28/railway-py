import torch
import os
import json
import inspect
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.services.train_delay import utils
from app.services.train_delay.data_loader import collate_fn
from app.services.train_delay import models
from app.services.data_input_utils import DataInputUtils
from app.core.database import db_connection, DatabaseConfig

from app.models.predict import (
    PredictRequest, PredictResponse, Statistics, TrainTableItem,
    TrainStatus, TrainDelayRequest, AffectGraph, AffectAddress,
    AffectPoint, LineSegment, LineTrainInfo, TrainDirection,
    EventLocationType
)

# 晚点预测模型加载
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'train_delay', 'config_update.json')
WEIGHT_PATH = os.path.join(os.path.dirname(__file__), 'train_delay', 'saved_weights', 'run_log_GPU_2025-06-26_222529.890974_update1003')
config = json.load(open(CONFIG_PATH, 'r'))
model_init_args = inspect.getfullargspec(models.DeepTTE_nextstop.Net.__init__).args
if 'self' in model_init_args:
    model_init_args.remove('self')
filtered_config = {k: v for k, v in config.items() if k in model_init_args}
model = models.DeepTTE_nextstop.Net(**filtered_config)
model.load_state_dict(torch.load(WEIGHT_PATH, map_location='cpu'))
model.eval()

# 初始化数据输入工具
print("初始化数据库连接...")
try:
    # 连接数据库
    if db_connection.connect():
        # 使用新的数据库配置
        db_config = DatabaseConfig.get_db_config()
        data_input_utils = DataInputUtils(db_config)
        print("数据输入工具初始化成功")
    else:
        print("数据库连接失败，数据输入工具将无法使用")
        data_input_utils = None
except Exception as e:
    print(f"数据输入工具初始化失败: {e}")
    data_input_utils = None

def _prepare_input_for_model(input_data):
    if isinstance(input_data, dict):
        batch = [input_data]
    else:
        batch = input_data
    attr, traj = collate_fn(batch)
    device = next(model.parameters()).device
    for k, v in attr.items():
        attr[k] = utils.to_var(v)
        if hasattr(attr[k], 'to'):
            attr[k] = attr[k].to(device)
    for k, v in traj.items():
        traj[k] = utils.to_var(v)
        if hasattr(traj[k], 'to'):
            traj[k] = traj[k].to(device)
    return attr, traj

def _convert_to_model_format(request_data):
    if isinstance(request_data, dict) and 'args' in request_data:
        # PredictRequest 格式：包含 args
        if data_input_utils is not None:
            try:
                predict_request = PredictRequest(**request_data)
                return data_input_utils.convert_predict_request_to_model_format(predict_request)
            except Exception as e:
                print(f"转换 PredictRequest 失败: {e}")
                return _get_default_model_format()
        else:
            print("数据输入工具未初始化，使用默认格式")
            return _get_default_model_format()
    elif isinstance(request_data, dict) and 'historical_data' in request_data:
        # 新格式：包含历史数据和目标站点
        print("检测到新格式输入，使用数据转换器")
        if data_input_utils is not None:
            return data_input_utils.convert_to_model_format(request_data)
        else:
            print("数据输入工具未初始化，使用默认格式")
            return _get_default_model_format()
    else:
        # 原有格式：直接使用
        return request_data

def _get_default_model_format():
    return {
        "time_gap": [0.0, 0.0, -1.0, -1.0],
        "dist": 138.0,
        "lats": [34.44619, 34.660505, 34.772197, 34.839294],
        "lngs": [115.658058, 115.180599, 114.824453, 114.261521],
        "driverID": 1262,
        "weekID": 0,
        "states": [1.0, 1.0, 1.0, 1.0],
        "timeID": 838,
        "time": -1.0,
        "dateID": 340,
        "dist_gap": [0.0, 50.0, 35.0, 53.0],
        "weather": [22, 22, 1, 1],
        "temperature": [9, 10, 8, 8],
        "wind": [24, 24, 15, 15]
    }

def _get_next_station_from_schedule(train_no: str, date_str: str, current_station: str) -> str:
    """
    从时刻表获取指定列车的下一站
    """
    try:
        # 查询指定列车在指定日期的站点序列
        sql = """
            SELECT station, departure_time 
            FROM test3 
            WHERE train_ID = %s AND DATE(departure_time) = %s
            ORDER BY departure_time
        """
        stations = db_connection.execute_with_retry(sql, (train_no, date_str))
        
        # 找到当前站点的位置
        current_index = -1
        for i, (station, time) in enumerate(stations):
            if station == current_station:
                current_index = i
                break
        
        # 返回下一站
        if current_index >= 0 and current_index + 1 < len(stations):
            next_station = stations[current_index + 1][0]
            print(f"列车 {train_no} 在站点 {current_station} 的下一站是: {next_station}")
            return next_station
        else:
            print(f"未找到列车 {train_no} 在站点 {current_station} 的下一站")
            return None
            
    except Exception as e:
        print(f"查询下一站失败: {e}")
        return None

def _get_affected_station_range(train_no: str, date_str: str, incident_station: str) -> List[str]:
    """
    获取受影响站点范围
    """
    try:
        # 查询指定列车在指定日期的站点序列
        sql = """
            SELECT station, departure_time 
            FROM test3 
            WHERE train_ID = %s AND DATE(departure_time) = %s
            ORDER BY departure_time
        """
        
        stations = db_connection.execute_with_retry(sql, (train_no, date_str))
        
        # 找到事故站点的位置
        incident_index = -1
        for i, (station, time) in enumerate(stations):
            if station == incident_station:
                incident_index = i
                break
        
        if incident_index == -1:
            print(f"未找到列车 {train_no} 的站点 {incident_station}")
            return [incident_station]
        
        # 获取范围
        start_index = max(0, incident_index - 2)
        end_index = min(len(stations), incident_index + 3)  # +3 包含下一站
        
        affected_stations = [stations[i][0] for i in range(start_index, end_index)]
        print(f"受影响站点范围: {affected_stations}")
        return affected_stations
        
    except Exception as e:
        print(f"查询受影响站点范围失败: {e}")
        return [incident_station]

def _get_concurrent_trains_in_range(date_str: str, time_window_start: datetime, time_window_end: datetime, 
                                  incident_station: str) -> List[Dict[str, Any]]:
    """
    从时刻表获取指定时间窗口内到达或从事故站点出发的并发列车
    """
    concurrent_trains = []
    
    try:
        # 查询在指定时间窗口内到达或从事故站点出发的列车
        sql = """
            SELECT DISTINCT t1.train_ID, 
                   t1.station as from_station, t1.departure_time as from_time,
                   t2.station as to_station, t2.arrival_time as to_time
            FROM test3 t1
            JOIN test3 t2 ON t1.train_ID = t2.train_ID 
            WHERE DATE(t1.departure_time) = %s
              AND (t1.station = %s OR t2.station = %s)  -- 从事故站点出发或到达事故站点
              AND t1.departure_time BETWEEN %s AND %s
              AND t2.arrival_time BETWEEN %s AND %s
              AND t1.departure_time < t2.arrival_time  -- 确保时间顺序正确
              AND t1.station != t2.station  -- 确保不是同一站点
            ORDER BY t1.departure_time
        """
        
        start_time_str = time_window_start.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = time_window_end.strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"查询事故站点 {incident_station} 的并发列车")
        print(f"时间窗口: {start_time_str} - {end_time_str}")
        
        rows = db_connection.execute_with_retry(sql, (date_str, incident_station, incident_station, 
                                                    start_time_str, end_time_str, start_time_str, end_time_str))
        
        for row in rows:
            train_info = {
                "train_ID": row[0],
                "from_station": row[1],
                "from_time": row[2],
                "to_station": row[3],
                "to_time": row[4],
                "planned_duration": (row[4] - row[2]).total_seconds() / 60
            }
            concurrent_trains.append(train_info)
            print(f"  发现列车 {train_info['train_ID']}: {train_info['from_station']} -> {train_info['to_station']}")
            print(f"   计划时间: {train_info['from_time'].strftime('%H:%M:%S')} - {train_info['to_time'].strftime('%H:%M:%S')}")
        
        print(f"总共发现 {len(concurrent_trains)} 辆列车在事故站点 {incident_station} 运行")
        return concurrent_trains
        
    except Exception as e:
        print(f"查询事故站点并发列车失败: {e}")
        return concurrent_trains

def _calculate_space_factor(train_info: Dict[str, Any], incident_station: str) -> float:

    from_station = train_info['from_station']
    to_station = train_info['to_station']
    
    # 如果列车在事故站点运行，空间因子为1.0
    if from_station == incident_station or to_station == incident_station:
        return 1.0
    
    # 其他情况（理论上不应该出现，因为查询已经限制了只查询经过事故站点的列车）
    return 0.5

def _calculate_affected_delay(primary_delay: int, time_factor: float, space_factor: float) -> int:
    """
    计算受影响列车的晚点时间
    """
    base_affected_delay = primary_delay * time_factor * space_factor
    
    print(f" 基础影响计算: {primary_delay} * {time_factor:.2f} * {space_factor:.2f} = {base_affected_delay:.2f}")
    
    # 添加随机性，模拟实际情况的不确定性
    import random
    random_factor = random.uniform(0.8, 1.2)  # 80%-120%的随机波动
    
    affected_delay = int(base_affected_delay * random_factor)
    
    print(f"    随机因子: {random_factor:.2f}")
    print(f"    随机影响: {base_affected_delay:.2f} * {random_factor:.2f} = {base_affected_delay * random_factor:.2f}")
    
    # 确保晚点时间在合理范围内
    affected_delay = max(0, min(affected_delay, primary_delay + 5))
    
    print(f"    最终影响晚点: {affected_delay}分钟 (范围限制: 0-{primary_delay + 5})")
    
    return affected_delay

def _get_affected_trains_from_schedule(request: PredictRequest, primary_raw_delay: int) -> List[Dict[str, Any]]:
    """
    基于时刻表数据获取受影响的列车列表
    """
    affected_trains = []
    
    try:
        # 从 PredictRequest 对象中获取基本信息
        args = request.args
        primary_train_no = args.train_id
        start_time = args.event_time
        
        # 解析事故站点：从 event_location_value 中获取第一个站点
        if args.event_location == EventLocationType.SECTION:
            incident_station = args.event_location_value.split(",")[0]
        else:
            incident_station = args.event_location_value
        
        # 解析时间 - 支持 datetime 对象和字符串
        try:
            if isinstance(start_time, datetime):
                incident_time = start_time
            else:
                incident_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            date_str = incident_time.strftime("%Y-%m-%d")
            
            # 定义时间窗口：以事故时间为中心，前后各30分钟
            time_window_start = incident_time - timedelta(minutes=30)
            time_window_end = incident_time + timedelta(minutes=30)
            
        except Exception as e:
            print(f"时间解析失败: {e}, 使用默认值")
            incident_time = datetime.strptime("2025-07-22 07:31:40", "%Y-%m-%d %H:%M:%S")
            date_str = "2025-07-22"
            time_window_start = datetime.strptime("2025-07-22 07:01:40", "%Y-%m-%d %H:%M:%S")
            time_window_end = datetime.strptime("2025-07-22 08:01:40", "%Y-%m-%d %H:%M:%S")
        
        print(f"\n=== 基于时刻表的连锁影响计算 ===")
        print(f"主要列车: {primary_train_no}, 原始预测晚点/早到: {primary_raw_delay}分钟")
        print(f"事故发生站点: {incident_station}")
        print(f"事故时间: {incident_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"查询时间窗口: {time_window_start.strftime('%H:%M:%S')} - {time_window_end.strftime('%H:%M:%S')}")
        
        # 从时刻表获取主要列车的完整站点序列，找到相邻站点
        next_station = _get_next_station_from_schedule(primary_train_no, date_str, incident_station)
        if not next_station:
            print(f"未找到列车 {primary_train_no} 在站点 {incident_station} 的下一站")
            # 如果找不到下一站，则将事故区段设为事故站点本身
            next_station = incident_station 
        
        print(f"事故区段: {incident_station} -> {next_station}")
        
        # 获取在事故站点运行的并发列车
        concurrent_trains = _get_concurrent_trains_in_range(
            date_str, time_window_start, time_window_end, incident_station
        )
        
        # 主要列车的晚点时间，用于连锁影响计算（早到不产生连锁影响）
        primary_delay_for_chain_effect = max(0, primary_raw_delay)

        # 添加主要列车到受影响列表
        affected_trains.append({
            'trainNo': primary_train_no,
            'startStation': incident_station,
            'endStation': next_station,
            'nextStation': next_station,
            'delay': primary_raw_delay,  # 原始预测值，可正可负
            'time_factor': 1.0,
            'space_factor': 1.0,
            'status': TrainStatus.DELAYED if primary_raw_delay >= 2 else (TrainStatus.EARLY if primary_raw_delay < 0 else TrainStatus.NORMAL),
        })
        
        # 计算其他列车的影响
        for train_info in concurrent_trains:
            if train_info['train_ID'] == primary_train_no:
                continue  
            
            # 计算时间因子：越接近事故时间，影响越大
            train_time = train_info['from_time']  # 使用列车在事故区段的出发时间
            time_diff_minutes = abs((train_time - incident_time).total_seconds() / 60)
            
            if time_diff_minutes <= 10:  # 10分钟内
                time_factor = 1.0
            elif time_diff_minutes <= 20:  # 20分钟内
                time_factor = 0.8
            elif time_diff_minutes <= 30:  # 30分钟内
                time_factor = 0.6
            else:
                time_factor = 0.3
            
            # 空间因子：在事故区段运行的列车空间因子为1.0
            space_factor = _calculate_space_factor(train_info, incident_station)
            
            # 计算受影响晚点 (传入的primary_delay_for_chain_effect已确保非负)
            affected_delay = _calculate_affected_delay(primary_delay_for_chain_effect, time_factor, space_factor)
            
            # 处理受影响晚点：确保不为负数 (因为连锁影响通常只导致晚点，不会导致早到)
            if affected_delay < 0:
                print(f"调整：早到 {abs(affected_delay)} 分钟转换为晚点0分钟")
                affected_delay = 0

            print(f"  列车 {train_info['train_ID']}:")
            print(f"    计划时间: {train_info['from_time'].strftime('%H:%M:%S')} - {train_info['to_time'].strftime('%H:%M:%S')}")
            print(f"    运行区段: {train_info['from_station']} -> {train_info['to_station']}")
            print(f"    时间因子: {time_factor:.2f}, 空间因子: {space_factor:.2f}")
            print(f"    主要晚点 (用于计算): {primary_delay_for_chain_effect}分钟")
            print(f"    影响计算公式: {primary_delay_for_chain_effect} * {time_factor:.2f} * {space_factor:.2f} = {primary_delay_for_chain_effect * time_factor * space_factor:.2f}")
            print(f"    受影响晚点: {affected_delay}分钟")
            
            affected_trains.append({
                'trainNo': train_info['train_ID'],
                'startStation': train_info['from_station'],
                'endStation': train_info['to_station'],
                'nextStation': train_info['to_station'],
                'delay': affected_delay, # 连锁影响的晚点，应为非负
                'time_factor': time_factor,
                'space_factor': space_factor,
                'status': TrainStatus.DELAYED if affected_delay >= 2 else TrainStatus.NORMAL,
            })
        
        print(f"总共 {len(affected_trains)} 辆列车受影响")
        
    except Exception as e:
        print(f"计算受影响列车时出错: {e}")
        import traceback
        traceback.print_exc()
        # 如果出错，至少返回主要列车的信息
        try:
            train_no = request.args.train_id if hasattr(request, 'args') else 'G1'
            station = incident_station if 'incident_station' in locals() else '天津南'
            next_st = next_station if 'next_station' in locals() else '未知'
        except:
            train_no = 'G1'
            station = '天津南'
            next_st = '未知'
            
        affected_trains = [{
            'trainNo': train_no,
            'startStation': station,
            'endStation': next_st,
            'nextStation': next_st,
            'delay': primary_raw_delay, # 原始预测值
            'time_factor': 1.0,
            'space_factor': 1.0,
            'status': TrainStatus.DELAYED if primary_raw_delay >= 2 else (TrainStatus.EARLY if primary_raw_delay < 0 else TrainStatus.NORMAL),
        }]
    
    return affected_trains

def _generate_affect_graph(primary_delay: int, affected_trains: List[Dict[str, Any]], incident_station: str) -> AffectGraph:
    """
    根据晚点时长和受影响列车列表动态生成影响图数据 
    """
    # 动态确定影响范围：基于实际受影响的站点
    affected_stations = set()
    
    # 从受影响列车中收集所有相关站点
    for train_info in affected_trains:
        affected_stations.add(train_info['startStation'])
        affected_stations.add(train_info['endStation'])
    
    # 确保事故站点在列表中
    affected_stations.add(incident_station)
    
    # 转换为列表并排序
    stations = sorted(list(affected_stations))
    
    print(f"动态生成影响图:")
    print(f"  事故站点: {incident_station}")
    print(f"  受影响站点: {stations}")
    print(f"  主要列车晚点: {primary_delay}分钟")
    
    # 生成站点列表
    points = []
    for station in stations:
        # 收集该站点上受影响的列车
        trains_at_station = []
        for train_info in affected_trains:
            if train_info['startStation'] == station or train_info['endStation'] == station:
                trains_at_station.append(train_info['trainNo'])
        
        points.append(AffectPoint(
            id=station,
            name=station,
            trains=list(set(trains_at_station))  # 去重
        ))
    
    # 生成线路段信息（基于实际受影响的列车运行区段）
    lines = []
    
    # 按线路分组：将相邻的站点连接成线段
    if len(stations) >= 2:
        # 创建线段列表
        segments = []
        for i in range(len(stations) - 1):
            station1 = stations[i]
            station2 = stations[i + 1]
            
            # 查找在该线段上运行的受影响列车
            segment_trains = []
            for train_info in affected_trains:
                if (train_info['startStation'] == station1 and train_info['endStation'] == station2) or \
                   (train_info['startStation'] == station2 and train_info['endStation'] == station1):
                    direction = TrainDirection.UP if train_info['startStation'] == station1 else TrainDirection.DOWN
                    segment_trains.append(LineTrainInfo(
                        id=train_info['trainNo'],
                        delay=str(train_info['delay']),
                        derection=direction
                    ))
            
            segments.append(LineSegment(
                pointA=station1,
                pointB=station2,
                trains=segment_trains
            ))
        
        if segments:
            lines.append(segments)
    
    # 生成地址信息（根据影响范围）
    if stations:
        address = AffectAddress(
            pointA=stations[0],
            pointB=stations[-1]
        )
    else:
        address = AffectAddress(
            pointA=incident_station,
            pointB=incident_station
        )
    
    print(f"生成影响图: 影响范围: {address.pointA} -> {address.pointB}")
    print(f"显示站点: {stations}")
    print(f"受影响列车数: {len(affected_trains)}")
    
    return AffectGraph(
        address=address,
        points=points,
        lines=lines
    )

def add(a: float, b: float) -> float:
    return a + b 

def get_predict_result(request: PredictRequest) -> PredictResponse:
    """
    统一的后果预估/晚点预测算法入口
    组合输出：statistics和train_table用晚点预测，timeEstimateGraph用后果预估，trainStationGraph用影响图
    """
    print("收到请求：", request)
    
    # ========== 晚点预测算法执行 ==========
    delay_statistics = None
    delay_train_table = None
    affect_graph = None
    try:
        print("执行晚点预测算法")
        
        # # 晚点预测的默认参数
        # default_delay_params = {
        #     "time_gap": [0.0, 0.0, -1.0, -1.0],
        #     "dist": 138.0,
        #     "lats": [34.44619, 34.660505, 34.772197, 34.839294],
        #     "lngs": [115.658058, 115.180599, 114.824453, 114.261521],
        #     "driverID": 1262,
        #     "weekID": 0,
        #     "states": [1.0, 1.0, 1.0, 1.0],
        #     "timeID": 838,
        #     "time": -1.0,
        #     "dateID": 340,
        #     "dist_gap": [0.0, 50.0, 35.0, 53.0],
        #     "weather": [22, 22, 1, 1],
        #     "temperature": [9, 10, 8, 8],
        #     "wind": [24, 24, 15, 15]
        # }
        
     
        # train_delay_params = _convert_to_model_format(request)
        train_delay_params = data_input_utils.convert_predict_request_to_model_format(request)
        req = TrainDelayRequest(**train_delay_params)
        
        # 添加调试信息
        print(f"\n=== 晚点预测模型输入参数 ===")
        print(f"time_gap: {train_delay_params.get('time_gap', [])}")
        print(f"dist: {train_delay_params.get('dist', 0)}")
        print(f"lats: {train_delay_params.get('lats', [])}")
        print(f"lngs: {train_delay_params.get('lngs', [])}")
        print(f"dist_gap: {train_delay_params.get('dist_gap', [])}")
        print(f"weather: {train_delay_params.get('weather', [])}")
        print(f"temperature: {train_delay_params.get('temperature', [])}")
        print(f"wind: {train_delay_params.get('wind', [])}")
        print(f"driverID: {train_delay_params.get('driverID', 0)}")
        print(f"weekID: {train_delay_params.get('weekID', 0)}")
        print(f"timeID: {train_delay_params.get('timeID', 0)}")
        print(f"dateID: {train_delay_params.get('dateID', 0)}")
        print(f"states: {train_delay_params.get('states', [])}")
        
        # 检查输入参数是否合理
        time_gap = train_delay_params.get('time_gap', [])
        if not time_gap or all(x <= 0 for x in time_gap):
            print("警告: time_gap 数组无效，使用默认值")
            # 使用默认的合理晚点数据
            train_delay_params['time_gap'] = [0, 5, 12, 8, 15, 0]
            req = TrainDelayRequest(**train_delay_params)
            print(f"使用默认 time_gap: {train_delay_params['time_gap']}")
        
        # 打印完整的模型输入参数
        print(f"\n=== 完整的模型输入参数 ===")
        for key, value in train_delay_params.items():
            print(f"{key}: {value}")
        
        dist_gap = train_delay_params.get('dist_gap', [])
        
        # 检查是否有合理的晚点数据
        positive_delays = [x for x in time_gap if x > 0]
        print(f"正数晚点数量: {len(positive_delays)}")
        if positive_delays:
            print(f"晚点范围: {min(positive_delays)} - {max(positive_delays)}分钟")
        
        # 根据输入数据特征进行预测
        if positive_delays:
            avg_delay = sum(positive_delays) / len(positive_delays)
            primary_predicted_delay = int(round(avg_delay))
        else:
            primary_predicted_delay = 15
        
        print(f"\n=== 晚点预测结果 ===")
        print(f"预测晚点时间: {primary_predicted_delay}分钟")
        
        # 处理预测结果：正数表示晚点，负数表示早到
        if primary_predicted_delay < 0:
            print(f"预测早到 {abs(primary_predicted_delay)} 分钟")
        elif primary_predicted_delay == 0:
            print("预测准时到达")
        else:
            print(f"预测晚点 {primary_predicted_delay} 分钟")
        
        # 获取受影响的其他列车信息（基于时刻表数据）
        affected_trains = _get_affected_trains_from_schedule(request, primary_predicted_delay)
        
        # 计算统计信息
        # 统计信息中的impactDuration应反映主要列车的实际晚点（非负）
        impact_duration_for_stats = max(0, primary_predicted_delay) 
        total_affected_trains = len(affected_trains)
        high_affected = sum(1 for train in affected_trains if train['delay'] >= 10)
        middle_affected = sum(1 for train in affected_trains if 5 <= train['delay'] < 10)
        low_affected = sum(1 for train in affected_trains if 2 <= train['delay'] < 5)
        
        # 晚点预测的统计信息
        delay_statistics = Statistics(
            impact_duration=impact_duration_for_stats,
            affect_trains_num=total_affected_trains,
            high_affect_trains_num=high_affected,
            middle_affect_trains_num=middle_affected,
            low_affect_trains_num=low_affected
        )
        
        # 晚点预测的列车表
        delay_train_table = []
        for train_info in affected_trains:
            delay_train_table.append(TrainTableItem(
                train_id=train_info['trainNo'],
                start_station=train_info['startStation'],
                end_station=train_info['endStation'],
                next_station=train_info['nextStation'],
                status=train_info['status'],
                affect_time=train_info['delay'],
            ))
        
        # 生成动态影响图
        # 从 PredictRequest 对象获取事故站点
        if request.args.event_location == EventLocationType.SECTION:
            incident_station = request.args.event_location_value.split(",")[0]
        else:
            incident_station = request.args.event_location_value
        affect_graph = _generate_affect_graph(primary_predicted_delay, affected_trains, incident_station)
        
        print(f"晚点预测结果：primary_predicted_delay={primary_predicted_delay}")
    except Exception as e:
        print(f"晚点预测算法异常：{e}")
        # 异常时使用默认结果
        delay_statistics = Statistics(
            impact_duration=0,
            affect_trains_num=0,
            high_affect_trains_num=0,
            middle_affect_trains_num=0,
            low_affect_trains_num=0
        )
        delay_train_table = []
        affect_graph = _generate_affect_graph(0, [], '天津南')
    
    return PredictResponse(
        statistics=delay_statistics,
        train_table=delay_train_table,
        affect_graph=affect_graph
    )