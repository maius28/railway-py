import pymysql
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys
import os


try:
    from app.models.predict import PredictRequest, EventArgs, EventType, UpDownType
except ImportError:
    # 如果导入失败，创建空的类定义
    class PredictRequest:
        def __init__(self, **kwargs):
            self.args = type('Args', (), kwargs.get('args', {}))()
    
    class EventArgs:
        pass
    
    class EventType:
        pass
    
    class UpDownType:
        pass

class DataInputUtils:
    def __init__(self, db_config: Dict[str, str]):
        """
        初始化数据输入工具
        """
        try:
            self.db = pymysql.connect(**db_config)
            self.cursor = self.db.cursor()
            print("数据库连接成功")
        except Exception as e:
            print(f"数据库连接失败: {e}")
            self.db = None
            self.cursor = None
        
        try:
            self.station_coordinates = self.load_station_coordinates()
            self.weather_mapping = self.load_weather_mapping()
            self.wind_mapping = self.load_wind_mapping()
            self.driver_mapping = self.load_driver_mapping()
            self.station_distances = self.load_station_distances()  # 从数据库加载距离
            self.historical_data = self.load_historical_data()  # 从数据库加载历史数据
            self.station_mapping = self.load_station_mapping()  # 加载中英文站点映射
            
        except Exception as e:
            print(f"初始化数据映射失败: {e}")
            self.station_coordinates = {}
            self.weather_mapping = {}
            self.wind_mapping = {}
            self.driver_mapping = {}
            self.station_distances = {}
            self.historical_data = {}
            self.station_mapping = {}

    def load_historical_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """从数据库加载历史列车数据"""
        if not self.cursor:
            print("数据库游标未初始化")
            return {}
        try:
            # 从test3表加载历史列车数据
            sql = "SELECT train_ID, station, arrival_time, departure_time FROM test3"
            self.cursor.execute(sql)
            
            historical_data = {}
            for row in self.cursor.fetchall():
                train_id = row[0]
                station = row[1]
                arrival_time = row[2]
                departure_time = row[3]
                
                if train_id not in historical_data:
                    historical_data[train_id] = []
                
                historical_data[train_id].append({
                    'station': station,
                    'arrival_time': arrival_time,
                    'departure_time': departure_time
                })
            
            print(f"从数据库加载了 {len(historical_data)} 辆列车的历史数据")
            for train_id, stations in list(historical_data.items())[:5]:  # 只显示前5辆列车
                print(f"  列车 {train_id}: {len(stations)} 个站点")
            
            return historical_data
        except Exception as e:
            print(f"从数据库加载历史数据失败: {e}")
            return {}

    def get_historical_stations_from_database(self, train_no: str, pre_station: str) -> List[str]:
        """从数据库获取历史站点序列"""
        if not self.cursor:
            print("数据库游标未初始化")
            return self._get_default_station_sequence()
        
        try:
            # 查询指定列车的历史站点
            sql = """
                SELECT DISTINCT station 
                FROM test3 
                WHERE train_ID = %s 
                ORDER BY departure_time
            """
            
            self.cursor.execute(sql, (train_no,))
            stations = [row[0] for row in self.cursor.fetchall()]
            
            # 过滤掉空字符串和None值
            stations = [station for station in stations if station and station.strip()]
            
            print(f"在数据库中查找车次 {train_no} 的历史数据")
            print(f"找到 {len(stations)} 个历史站点")
            
            if not stations:
                print("未找到历史数据，使用默认站点序列")
                return self._get_default_station_sequence()
            
            # 找到pre_station在序列中的位置
            try:
                pre_station_index = stations.index(pre_station)
                # 返回pre_station及其之前的站点
                result_stations = stations[:pre_station_index + 1]
                print(f"找到站点 '{pre_station}' 在位置 {pre_station_index}")
                print(f"返回站点序列: {result_stations}")
                return result_stations
            except ValueError:
                print(f"警告: 未找到站点 '{pre_station}' 在历史数据中")
                print(f"历史站点: {stations}")
                # 如果找不到pre_station，返回前几个站点
                return stations[:min(4, len(stations))]
                
        except Exception as e:
            print(f"从数据库获取历史站点失败: {e}")
            return self._get_default_station_sequence()

    def _get_default_station_sequence(self) -> List[str]:
        """获取默认的站点序列"""
        return ["北京南", "廊坊", "天津南", "沧州西", "德州东", "济南西"]

    def load_station_coordinates(self) -> Dict[str, Dict[str, float]]:
        """从数据库加载站点坐标"""
        if not self.cursor:
            print("数据库游标未初始化")
            return {}
        try:
            # 从jinghu_station表加载站点坐标
            sql = "SELECT zh_name, en_name, longitude, latitude FROM jinghu_station"
            self.cursor.execute(sql)
            
            coordinates = {}
            for row in self.cursor.fetchall():
                zh_name = row[0]  # 中文站点名称
                en_name = row[1]  # 英文站点名称
                longitude = float(row[2])  # 经度
                latitude = float(row[3])   # 纬度
                
                # 存储中文站点名称的坐标
                coordinates[zh_name] = {"lng": longitude, "lat": latitude}
                # 存储英文站点名称的坐标
                coordinates[en_name] = {"lng": longitude, "lat": latitude}
                # 存储去掉"站"字的中文名称
                if zh_name.endswith("站"):
                    short_name = zh_name.replace("站", "")
                    coordinates[short_name] = {"lng": longitude, "lat": latitude}
            
            print(f"从数据库加载了 {len(coordinates)} 个站点坐标")
            return coordinates
        except Exception as e:
            print(f"从数据库加载站点坐标失败: {e}")
            return {}

    def load_weather_mapping(self) -> Dict[str, int]:
        """从数据库加载天气映射"""
        if not self.cursor:
            print("数据库游标未初始化")
            return {}
        try:
            # 从weather表加载天气映射
            sql = "SELECT name, code FROM weather"
            self.cursor.execute(sql)
            
            weather_mapping = {}
            for row in self.cursor.fetchall():
                weather_name = row[0]
                weather_code = row[1]
                weather_mapping[weather_name] = weather_code
            
            print(f"从数据库加载了 {len(weather_mapping)} 个天气映射")
            return weather_mapping
        except Exception as e:
            print(f"从数据库加载天气映射失败: {e}")
            return {}

    def load_wind_mapping(self) -> Dict[str, int]:
        """从数据库加载风速映射"""
        if not self.cursor:
            print("数据库游标未初始化")
            return {}
        try:
            # 从wind表加载风速映射
            sql = "SELECT name, code FROM wind"
            self.cursor.execute(sql)
            
            wind_mapping = {}
            for row in self.cursor.fetchall():
                wind_name = row[0]
                wind_code = row[1]
                wind_mapping[wind_name] = wind_code
            
            print(f"从数据库加载了 {len(wind_mapping)} 个风速映射")
            return wind_mapping
        except Exception as e:
            print(f"从数据库加载风速映射失败: {e}")
            return {}

    def load_driver_mapping(self) -> Dict[str, int]:
        """加载列车车次映射"""
        if not self.cursor:
            return {}
        try:
            sql = "SELECT train_no, code FROM train_number"
            self.cursor.execute(sql)
            return {row[0]: int(row[1]) for row in self.cursor.fetchall()}
        except Exception as e:
            print(f"加载列车车次映射失败: {e}")
            return {}

    def load_station_mapping(self) -> Dict[str, str]:
        """从数据库加载中英文站点映射"""
        if not self.cursor:
            print("数据库游标未初始化")
            return {}
        try:
            # 从data_adj表加载所有站点名称并创建映射
            sql = "SELECT DISTINCT from_station, to_station FROM data_adj"
            self.cursor.execute(sql)
            
            station_mapping = {}
            for row in self.cursor.fetchall():
                from_station = row[0]
                to_station = row[1]
                
                # 提取中文站点名称（去掉"Railway Station"等英文后缀）
                if "Railway Station" in from_station:
                    chinese_name = from_station.replace(" Railway Station", "")
                    station_mapping[chinese_name] = from_station
                if "Railway Station" in to_station:
                    chinese_name = to_station.replace(" Railway Station", "")
                    station_mapping[chinese_name] = to_station
            
            # 添加常见的中文站点名称映射
            common_mappings = {
                "北京南": "Beijingnan Railway Station",
                "廊坊": "Langfang Railway Station", 
                "天津南": "Tianjinnan Railway Station",
                "沧州西": "Cangzhouxi Railway Station",
                "德州东": "Dezhoudong Railway Station",
                "济南西": "Jinanxi Railway Station",
                "泰安": "Taian Railway Station",
                "曲阜东": "Qufudong Railway Station",
                "淄博": "Zibo Railway Station",
                "青岛": "Qingdao Railway Station",
                "聊城": "Liaocheng Railway Station",
                "菏泽": "Heze Railway Station",
                "德州": "Dezhou Railway Station",
                "济南": "Jinan Railway Station",
                "天津": "Tianjin Railway Station",
                "北京": "Beijing Railway Station"
            }
            
            # 合并映射
            station_mapping.update(common_mappings)
            
            print(f"从数据库加载了 {len(station_mapping)} 个中英文站点映射")
            return station_mapping
        except Exception as e:
            print(f"从数据库加载中英文站点映射失败: {e}")
            return {}

    def load_station_distances(self) -> Dict[tuple, float]:
        """从数据库加载站点距离"""
        if not self.cursor:
            print("数据库游标未初始化")
            return {}
        try:
            # 从data_adj表加载距离数据
            sql = "SELECT from_station, to_station, mileage FROM data_adj"
            self.cursor.execute(sql)
            
            dist_dict = {}
            sample_count = 0
            for row in self.cursor.fetchall():
                from_station = row[0]
                to_station = row[1]
                distance = float(row[2])
                dist_dict[(from_station, to_station)] = distance
                dist_dict[(to_station, from_station)] = distance
                
                # 显示前10个样本用于调试
                if sample_count < 10:
                    print(f"样本距离数据: '{from_station}' -> '{to_station}' = {distance}km")
                    sample_count += 1
            
            print(f"总共从数据库加载了 {len(dist_dict)//2} 对站点距离")
            return dist_dict
        except Exception as e:
            print(f"从数据库加载站点距离失败: {e}")
            return {}

    def get_station_coordinates(self, station_name: str) -> Dict[str, float]:
        """获取站点坐标"""
        coords = self.station_coordinates.get(station_name, {"lng": 0.0, "lat": 0.0})
        if coords["lng"] == 0.0 and coords["lat"] == 0.0:
            station_with_zhan = station_name + "站"
            coords = self.station_coordinates.get(station_with_zhan, {"lng": 0.0, "lat": 0.0})
            if coords["lng"] != 0.0 or coords["lat"] != 0.0:
                print(f"找到站点坐标: {station_name} -> {station_with_zhan} -> ({coords['lng']}, {coords['lat']})")
            else:
                station_without_zhan = station_name.replace("站", "")
                coords = self.station_coordinates.get(station_without_zhan, {"lng": 0.0, "lat": 0.0})
                if coords["lng"] != 0.0 or coords["lat"] != 0.0:
                    print(f"找到站点坐标: {station_name} -> {station_without_zhan} -> ({coords['lng']}, {coords['lat']})")
                else:
                    print(f"警告: 未找到站点 '{station_name}' 的坐标，使用默认值 (0.0, 0.0)")
        else:
            print(f"获取站点坐标: {station_name} -> ({coords['lng']}, {coords['lat']})")
        
        return coords

    def get_station_distance(self, station1: str, station2: str) -> float:
        """获取站点间距离"""
        print(f"正在查找距离: '{station1}' -> '{station2}'")
        
        # 从数据库映射获取英文站点名称
        eng_station1 = self.station_mapping.get(station1, station1)
        eng_station2 = self.station_mapping.get(station2, station2)
        
        print(f"  中文站点: {station1} -> {station2}")
        print(f"  英文站点: {eng_station1} -> {eng_station2}")
        match_attempts = [
            (station1, station2),  # 中文直接匹配
            (eng_station1, eng_station2),  # 英文直接匹配
            (station1 + "站", station2 + "站"),  # 中文都加"站"字
            (eng_station1, eng_station2),  # 英文匹配
        ]
        
        if not station1.endswith("站"):
            match_attempts.append((station1 + "站", station2))
        if not station2.endswith("站"):
            match_attempts.append((station1, station2 + "站"))
        
        if eng_station1 != station1:
            match_attempts.append((eng_station1, eng_station2))
        if eng_station2 != station2:
            match_attempts.append((eng_station1, eng_station2))
        
        if "Railway Station" not in station1 and "Railway Station" not in station2:
            # 如果输入的是中文，尝试转换为英文格式
            eng1 = station1 + " Railway Station"
            eng2 = station2 + " Railway Station"
            match_attempts.append((eng1, eng2))
        
        for direction in ["南", "北", "东", "西"]:
            if station1.endswith(direction):
                base1 = station1[:-1]
                match_attempts.append((base1, station2))
                match_attempts.append((base1 + " Railway Station", station2 + " Railway Station"))
            if station2.endswith(direction):
                base2 = station2[:-1]
                match_attempts.append((station1, base2))
                match_attempts.append((station1 + " Railway Station", base2 + " Railway Station"))
        
        print(f"  可用的距离数据样本:")
        sample_count = 0
        for (s1, s2), dist in self.station_distances.items():
            if sample_count < 5:
                print(f"    '{s1}' -> '{s2}' = {dist}km")
                sample_count += 1
        
        for i, (s1, s2) in enumerate(match_attempts, 1):
            print(f"  {i}. '{s1}' -> '{s2}'")
            if (s1, s2) in self.station_distances:
                distance = self.station_distances[(s1, s2)]
                print(f"  ✅ 匹配成功: {s1} -> {s2} = {distance}km")
                return distance
        
        print(f"  ❌ 所有匹配方式都失败，未找到站点 '{station1}' 到 '{station2}' 的距离")
        print(f"    尝试过的匹配方式:")
        for i, (s1, s2) in enumerate(match_attempts, 1):
            print(f"      {i}. '{s1}' -> '{s2}'")
        print(f"  结果: {station1} -> {station2} = 0.0km")
        return 0.0

    def get_weather_code(self, weather: str) -> int:
        """获取天气代码"""
        if isinstance(weather, int):
            return weather
        return self.weather_mapping.get(weather, 22)

    def get_wind_code(self, wind: str) -> int:
        """获取风速代码"""
        if isinstance(wind, int):
            return wind
        return self.wind_mapping.get(wind, 24)

    def get_driver_id(self, train_no: str) -> int:
        """获取司机ID"""
        return self.driver_mapping.get(train_no, 1262)

    def calculate_time_id(self, time_str: str) -> int:
        """计算时间ID"""
        try:
            time_obj = datetime.strptime(time_str, "%H:%M:%S")
            return time_obj.hour * 60 + time_obj.minute
        except:
            return 838

    def calculate_date_id(self, date_str: str) -> int:
        """计算日期ID"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return (date_obj.year - 2020) * 365 + date_obj.timetuple().tm_yday
        except:
            return 340

    def calculate_week_id(self, date_str: str) -> int:
        """计算是否是假期"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.weekday()
        except:
            return 0

    def generate_random_delay(self) -> int:
        """生成随机晚点时间"""
        return random.randint(0, 30)

    def convert_predict_request_to_model_format_simple(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 PredictRequest 格式转换为模型输入格式
        """
        try:
            args = request_data.get('args', {})
            
            # 获取基本信息
            train_no = args.get('trainNo', 'G1')
            start_time = args.get('startTime', '2025-07-22 08:00:00')
            pre_station = args.get('preStation', '济南西')
            next_station = args.get('nextStation', '泰安')
            
            # 解析时间
            try:
                time_obj = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                date_str = time_obj.strftime("%Y-%m-%d")
                time_str = time_obj.strftime("%H:%M:%S")
            except:
                time_obj = datetime.strptime("2025-07-22 08:00:00", "%Y-%m-%d %H:%M:%S")
                date_str = "2025-07-22"
                time_str = "08:00:00"
            
            # 获取历史站点信息
            historical_stations = self.get_historical_stations_from_database(train_no, pre_station)
            
            # 生成站点序列
            station_sequence = []
            for station_info in historical_stations:
                station_sequence.append(station_info)
            
            # 添加目标站点
            if next_station not in station_sequence:
                station_sequence.append(next_station)
            
            # 生成坐标和距离数据
            lats = []
            lngs = []
            dist_gap = []
            time_gap = []
            
            for i, station in enumerate(station_sequence):
                coords = self.get_station_coordinates(station)
                lats.append(coords['lat'])
                lngs.append(coords['lng'])
                
                if i == 0:
                    # 起始站点的距离为0，晚点时间为0
                    dist_gap.append(0.0)
                    time_gap.append(0)
                else:
                    # 计算距离
                    prev_station = station_sequence[i-1]
                    distance = self.get_station_distance(prev_station, station)
                    dist_gap.append(distance)
                    
                    delay = self.generate_random_delay()
                    time_gap.append(delay)
        
            while len(lats) < 4:
                lats.append(0.0)
                lngs.append(0.0)
                dist_gap.append(0.0)
                time_gap.append(0)
            
            # 构造模型输入格式
            model_input = {
                "time_gap": time_gap[:4],
                "dist": sum(dist_gap),
                "lats": lats[:4],
                "lngs": lngs[:4],
                "driverID": self.get_driver_id(train_no),
                "weekID": self.calculate_week_id(date_str),
                "states": [1.0] * 4,
                "timeID": self.calculate_time_id(time_str),
                "time": -1.0,
                "dateID": self.calculate_date_id(date_str),
                "dist_gap": dist_gap[:4],
                "weather": [22, 22, 1, 1],
                "temperature": [9, 10, 8, 8],
                "wind": [24, 24, 15, 15]
            }
            
            print(f"转换结果:")
            print(f"  time_gap: {model_input['time_gap']}")
            print(f"  dist: {model_input['dist']}")
            print(f"  lats: {model_input['lats']}")
            print(f"  lngs: {model_input['lngs']}")
            print(f"  dist_gap: {model_input['dist_gap']}")
            
            return model_input
            
        except Exception as e:
            print(f"转换失败: {e}")
            return self._get_default_format()

    def convert_predict_request_to_model_format(self, predict_request: PredictRequest) -> Dict[str, Any]:
        """
        将 PredictRequest 对象转换为模型输入格式
        """
        try:
            args = predict_request.args
            
            # 获取基本信息
            train_no = args.trainNo
            start_time = args.startTime
            pre_station = args.preStation
            next_station = args.nextStation
            
            # 解析时间
            try:
                time_obj = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                date_str = time_obj.strftime("%Y-%m-%d")
                time_str = time_obj.strftime("%H:%M:%S")
            except:
                time_obj = datetime.strptime("2025-07-22 08:00:00", "%Y-%m-%d %H:%M:%S")
                date_str = "2025-07-22"
                time_str = "08:00:00"
            
            # 获取历史站点信息
            historical_stations = self.get_historical_stations_from_database(train_no, pre_station)
            
            # 生成站点序列
            station_sequence = []
            for station_info in historical_stations:
                station_sequence.append(station_info)
            
            # 添加目标站点
            if next_station not in station_sequence:
                station_sequence.append(next_station)
            
            # 生成坐标和距离数据
            lats = []
            lngs = []
            dist_gap = []
            time_gap = []
            
            for i, station in enumerate(station_sequence):
                coords = self.get_station_coordinates(station)
                lats.append(coords['lat'])
                lngs.append(coords['lng'])
                
                if i == 0:
                    #起始站点的距离为0，晚点时间为0
                    dist_gap.append(0.0)
                    time_gap.append(0)
                else:
                    # 计算距离
                    prev_station = station_sequence[i-1]
                    distance = self.get_station_distance(prev_station, station)
                    dist_gap.append(distance)
                    
            
                    delay = self.generate_random_delay()
                    time_gap.append(delay)
            
            
            while len(lats) < 4:
                lats.append(0.0)
                lngs.append(0.0)
                dist_gap.append(0.0)
                time_gap.append(0)
            
            # 构造模型输入格式
            model_input = {
                "time_gap": time_gap[:4],
                "dist": sum(dist_gap),
                "lats": lats[:4],
                "lngs": lngs[:4],
                "driverID": self.get_driver_id(train_no),
                "weekID": self.calculate_week_id(date_str),
                "states": [1.0] * 4,
                "timeID": self.calculate_time_id(time_str),
                "time": -1.0,
                "dateID": self.calculate_date_id(date_str),
                "dist_gap": dist_gap[:4],
                "weather": [22, 22, 1, 1],
                "temperature": [9, 10, 8, 8],
                "wind": [24, 24, 15, 15]
            }
            
            print(f"转换结果:")
            print(f"  time_gap: {model_input['time_gap']}")
            print(f"  dist: {model_input['dist']}")
            print(f"  lats: {model_input['lats']}")
            print(f"  lngs: {model_input['lngs']}")
            print(f"  dist_gap: {model_input['dist_gap']}")
            
            return model_input
            
        except Exception as e:
            print(f"转换失败: {e}")
            return self._get_default_format()

    def convert_to_model_format(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将新格式的输入数据转换为模型输入格式
        """
        try:
            historical_data = input_data.get('historical_data', [])
            target_station = input_data.get('target_station', '济南西')
            
            # 生成站点序列
            station_sequence = []
            for station_info in historical_data:
                station_sequence.append(station_info['station'])
            
            # 添加目标站点
            if target_station not in station_sequence:
                station_sequence.append(target_station)
            
            # 生成坐标和距离数据
            lats = []
            lngs = []
            dist_gap = []
            time_gap = []
            
            for i, station in enumerate(station_sequence):
                coords = self.get_station_coordinates(station)
                lats.append(coords['lat'])
                lngs.append(coords['lng'])
                
                if i == 0:
                    # 第一个站点（起始站点）的距离为0，晚点时间为0
                    dist_gap.append(0.0)
                    time_gap.append(0)
                else:
                    # 计算距离（从当前站点到下一个站点的距离）
                    prev_station = station_sequence[i-1]
                    distance = self.get_station_distance(prev_station, station)
                    dist_gap.append(distance)
                    
                
                    delay = self.generate_random_delay()
                    time_gap.append(delay)
            
            
            while len(lats) < 4:
                lats.append(0.0)
                lngs.append(0.0)
                dist_gap.append(0.0)
                time_gap.append(0)
            
            # 构造模型输入格式
            model_input = {
                "time_gap": time_gap[:4],
                "dist": sum(dist_gap),
                "lats": lats[:4],
                "lngs": lngs[:4],
                "driverID": 1262,
                "weekID": 0,
                "states": [1.0] * 4,
                "timeID": 838,
                "time": -1.0,
                "dateID": 340,
                "dist_gap": dist_gap[:4],
                "weather": [22, 22, 1, 1],
                "temperature": [9, 10, 8, 8],
                "wind": [24, 24, 15, 15]
            }
            
            print(f"转换结果:")
            print(f"  time_gap: {model_input['time_gap']}")
            print(f"  dist: {model_input['dist']}")
            print(f"  lats: {model_input['lats']}")
            print(f"  lngs: {model_input['lngs']}")
            print(f"  dist_gap: {model_input['dist_gap']}")
            
            return model_input
            
        except Exception as e:
            print(f"转换失败: {e}")
            return self._get_default_format()

    def _get_default_format(self) -> Dict[str, Any]:
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