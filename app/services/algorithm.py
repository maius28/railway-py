# 示例算法服务



from app.models.predict import (
    PredictRequest, PredictResponse, TimeEstimateGraph, Statistics, 
    TrainTableItem, TrainStationGraph, TimePoint, PointStatus, 
    TrainStatus, TimeUnit
)


def add(a: float, b: float) -> float:
    return a + b 

def get_predict_result(request: PredictRequest) -> PredictResponse:
    # 这里可以实现后果预估算法的具体逻辑
    # 返回固定的预测结果
    
    # 创建时间估算图
    time_estimate_graph = TimeEstimateGraph(
        mermaidInfo="graph TD; A[开始] --> B[评估影响]; B --> C[制定方案]; C --> D[执行措施]; D --> E[结束]",
        points=[
            {"A": TimePoint(status=PointStatus.COMPLETED, predictTime=10)},
            {"B": TimePoint(status=PointStatus.PROCESSING, predictTime=15)},
            {"C": TimePoint(status=PointStatus.PENDING, predictTime=20)},
            {"D": TimePoint(status=PointStatus.PENDING, predictTime=30)}
        ]
    )
    
    # 创建统计信息
    statistics = Statistics(
        impactDuration=111,
        affectTrainsNum=222,
        highAffectTrainsNum=11,
        middleAffectTrainsNum=11,
        lowAffectTrainsNum=200
    )
    
    # 创建列车表
    train_table = [
        TrainTableItem(
            trainNo="G123",
            startStation="北京南",
            endStation="上海虹桥",
            nextStation="天津南",
            status=TrainStatus.DELAYED,
            affectTime=30,
            timeUnit=TimeUnit.MINUTE
        ),
        TrainTableItem(
            trainNo="D456",
            startStation="上海虹桥",
            endStation="杭州东",
            nextStation="嘉兴南",
            status=TrainStatus.NORMAL,
            affectTime=0,
            timeUnit=TimeUnit.MINUTE
        ),
        TrainTableItem(
            trainNo="K789",
            startStation="广州",
            endStation="深圳",
            nextStation="东莞",
            status=TrainStatus.REROUTED,
            affectTime=2,
            timeUnit=TimeUnit.HOUR
        )
    ]
    
    # 创建列车站点图（暂时为空）
    train_station_graph = TrainStationGraph()
    
    # 构造并返回预测响应
    return PredictResponse(
        timeEstimateGraph=time_estimate_graph,
        statistics=statistics,
        trainTable=train_table,
        trainStationGraph=train_station_graph
    )