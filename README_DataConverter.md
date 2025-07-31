# 数据转换工具使用说明

## 概述

这个数据转换工具用于将前端输入的实际应用格式转换为晚点预测模型的标准输入格式。支持从数据库获取站点信息、天气数据、距离数据等。

## 功能特性

1. **支持多种输入格式**：字符串和数字格式的天气、风速、温度数据
2. **数据库映射**：自动从数据库获取站点经纬度、距离信息
3. **随机晚点生成**：当实际晚点时间不可用时，自动生成随机值
4. **输入验证**：验证输入格式的正确性
5. **错误处理**：提供默认值和异常处理

## 数据库表结构

工具支持以下数据库表：

- **jinghu_station**：站点经纬度信息
- **weather**：天气类型映射
- **wind**：风速类型映射
- **train_number**：列车和司机ID映射
- **date**：日期相关计算
- **距离表**：相邻站点距离信息

## 输入格式

### 前端输入格式（图2黄框）

```json
{
  "historical_data": {
    "stations": [
      {
        "station_name": "北京南",
        "lng": 116.378517,
        "lat": 39.865246,
        "actual_delay": 0,
        "weather": "晴天",
        "wind": "无风",
        "temperature": "常温",
        "arrival_time": "2024-06-01 10:00:00"
      },
      {
        "station_name": "天津南", 
        "lng": 117.355072,
        "lat": 39.084158,
        "actual_delay": 5,
        "weather": 22,
        "wind": 24,
        "temperature": 10,
        "arrival_time": "2024-06-01 10:30:00"
      }
    ]
  },
  "target_station": {
    "station_name": "济南西",
    "lng": 116.968291,
    "lat": 36.651216,
    "weather": "多云",
    "wind": "微风",
    "temperature": "低温",
    "expected_arrival": "2024-06-01 11:00:00"
  },
  "train_info": {
    "train_id": "G123",
    "driver_id": 1262,
    "date": "2024-06-01",
    "time": "10:00",
    "week_id": 0
  }
}
```

### 模型标准输入格式

```json
{
  "time_gap": [0, 5, 8],
  "dist": 256.4,
  "lats": [39.865246, 39.084158, 36.651216],
  "lngs": [116.378517, 117.355072, 116.968291],
  "driverID": 1262,
  "weekID": 0,
  "states": [1.0, 1.0, 1.0],
  "timeID": 410,
  "time": -1.0,
  "dateID": 152,
  "dist_gap": [85.2, 171.2, 0.0],
  "weather": [22, 22, 23],
  "temperature": [9, 10, 8],
  "wind": [24, 24, 25]
}
```

## 使用方法

### 1. 基本使用

```python
from app.services.data_converter import DataConverter

# 初始化转换器
converter = DataConverter()

# 前端输入数据
frontend_input = {
    "historical_data": {
        "stations": [
            {
                "station_name": "北京南",
                "weather": "晴天",
                "wind": "无风",
                "temperature": "常温",
                "arrival_time": "2024-06-01 10:00:00"
            }
        ]
    },
    "target_station": {
        "station_name": "济南西",
        "weather": "多云",
        "wind": "微风",
        "temperature": "低温",
        "expected_arrival": "2024-06-01 11:00:00"
    },
    "train_info": {
        "train_id": "G123",
        "date": "2024-06-01",
        "time": "10:00"
    }
}

# 验证输入格式
if converter.validate_input_format(frontend_input):
    # 转换为模型格式
    model_input = converter.convert_to_model_format(frontend_input)
    print("转换成功！")
else:
    print("输入格式错误！")
```

### 2. 与算法集成

```python
from app.services.algorithm import get_predict_result

# 直接使用前端输入调用算法
result = get_predict_result(frontend_input)
print("预测结果：", result)
```

## 数据库映射

### 天气映射
```python
weather_mapping = {
    "晴天": 22,
    "多云": 23,
    "阴天": 24,
    "小雨": 25,
    "中雨": 26,
    "大雨": 27,
    "雪": 28,
    "雾": 29,
    "霾": 30
}
```

### 风速映射
```python
wind_mapping = {
    "无风": 24,
    "微风": 25,
    "小风": 26,
    "中风": 27,
    "大风": 28,
    "强风": 29,
    "台风": 30
}
```

### 温度映射
```python
temperature_mapping = {
    "低温": 8,
    "常温": 9,
    "高温": 10,
    "极寒": 7,
    "极热": 11
}
```

## 支持的站点

工具支持以下站点的自动经纬度获取：

- 北京南
- 廊坊
- 天津南
- 沧州西
- 德州东
- 济南西
- 泰安
- 曲阜东
- 滕州东
- 枣庄
- 徐州东
- 宿州东
- 蚌埠南
- 定远
- 滁州
- 南京南
- 镇江南
- 丹阳北
- 常州北
- 无锡东
- 苏州北
- 昆山南
- 上海虹桥

## 距离计算

工具内置了相邻站点之间的距离表，支持以下路线：

- 北京南 -> 廊坊: 60.5 km
- 廊坊 -> 天津南: 85.2 km
- 天津南 -> 沧州西: 120.8 km
- 沧州西 -> 德州东: 95.3 km
- 德州东 -> 济南西: 110.7 km
- 济南西 -> 泰安: 65.4 km
- 泰安 -> 曲阜东: 78.9 km
- 曲阜东 -> 滕州东: 45.6 km
- 滕州东 -> 枣庄: 52.3 km
- 枣庄 -> 徐州东: 88.7 km
- 徐州东 -> 宿州东: 95.2 km
- 宿州东 -> 蚌埠南: 76.8 km
- 蚌埠南 -> 定远: 89.4 km
- 定远 -> 滁州: 67.3 km
- 滁州 -> 南京南: 82.1 km
- 南京南 -> 镇江南: 68.5 km
- 镇江南 -> 丹阳北: 45.2 km
- 丹阳北 -> 常州北: 58.7 km
- 常州北 -> 无锡东: 73.4 km
- 无锡东 -> 苏州北: 52.8 km
- 苏州北 -> 昆山南: 41.6 km
- 昆山南 -> 上海虹桥: 35.9 km

## 测试

运行测试脚本：

```bash
python test_data_converter.py
```

运行使用示例：

```bash
python example_usage.py
```

## 注意事项

1. **实际晚点时间**：暂时拿不到实际晚点时间，使用随机值代替
2. **数据库连接**：当前使用模拟数据，实际使用时需要连接真实数据库
3. **输入验证**：建议在使用前验证输入格式
4. **错误处理**：工具提供默认值和异常处理机制

## 文件结构

```
app/services/
├── data_converter.py      # 数据转换工具
├── algorithm.py           # 算法集成
└── train_delay/          # 晚点预测模型

test_data_converter.py     # 测试脚本
example_usage.py          # 使用示例
README_DataConverter.md   # 说明文档
``` 