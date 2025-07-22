# 示例算法服务

from app.models.predict import (
    PredictRequest, PredictResponse, Statistics, TrainTableItem, 
    EventGraphNode, EventNodeStatus, TrainStatus, AffectGraph,
    AffectAddress, AffectPoint, LineSegment, LineTrainInfo, TrainDirection
)


def add(a: float, b: float) -> float:
    return a + b 

def get_predict_result(request: PredictRequest) -> PredictResponse:
    # 这里可以实现后果预估算法的具体逻辑
    # 返回固定的预测结果
    
    # 创建事件图
    event_graph = {
        "A": EventGraphNode(
            description="司机发现接触网上挂有异物",
            predict_time="10s",
            real_time="10s",
            status=EventNodeStatus.PENDING
        ),
        "B": EventGraphNode(
            description="司机通知处理",
            predict_time="100s",
            real_time="10s",
            status=EventNodeStatus.PENDING
        ),
        "C": EventGraphNode(
            description="路段清理",
            predict_time="10min",
            real_time="10s",
            status=EventNodeStatus.PENDING
        ),
        "END": EventGraphNode(
            description="结束",
            predict_time="",
            status=EventNodeStatus.PENDING
        )
    }
    
    # 创建统计信息
    statistics = Statistics(
        impact_duration=111,
        affect_trains_num=222,
        high_affect_trains_num=11,
        middle_affect_trains_num=11,
        low_affect_trains_num=200
    )
    
    # 创建列车表
    train_table = [
        TrainTableItem(
            train_id="G123",
            start_station="北京南",
            end_station="上海虹桥",
            next_station="天津南",
            status=TrainStatus.DELAYED,
            affect_time=30
        ),
        TrainTableItem(
            train_id="D456",
            start_station="上海虹桥",
            end_station="杭州东",
            next_station="嘉兴南",
            status=TrainStatus.NORMAL,
            affect_time=0
        ),
        TrainTableItem(
            train_id="K789",
            start_station="广州",
            end_station="深圳",
            next_station="东莞",
            status=TrainStatus.REROUTED,
            affect_time=120
        )
    ]
    
    # 创建影响图
    affect_graph = AffectGraph(
        address=AffectAddress(
            pointA="曲阜东",
            pointB="曲阜东"
        ),
        points=[
            AffectPoint(id="德州东", name="德州东", trains=[]),
            AffectPoint(id="济南西", name="济南西", trains=[]),
            AffectPoint(id="泰安", name="泰安", trains=[]),
            AffectPoint(id="曲阜东", name="曲阜东", trains=[]),
            AffectPoint(id="淄博", name="淄博", trains=[]),
            AffectPoint(id="青岛", name="青岛", trains=[]),
            AffectPoint(id="聊城", name="聊城", trains=[]),
            AffectPoint(id="菏泽", name="菏泽", trains=[])
        ],
        lines=[
            [
                LineSegment(
                    pointA="德州东",
                    pointB="济南西",
                    trains=[
                        LineTrainInfo(id="G201", delay="30", derection=TrainDirection.UP)
                    ]
                ),
                LineSegment(
                    pointA="济南西",
                    pointB="泰安",
                    trains=[
                        LineTrainInfo(id="G29", delay="90", derection=TrainDirection.UP),
                        LineTrainInfo(id="G31", delay="90", derection=TrainDirection.UP)
                    ]
                ),
                LineSegment(
                    pointA="泰安",
                    pointB="曲阜东",
                    trains=[
                        LineTrainInfo(id="G401", delay="30", derection=TrainDirection.UP)
                    ]
                )
            ],
            [
                LineSegment(
                    pointA="济南西",
                    pointB="淄博",
                    trains=[]
                ),
                LineSegment(
                    pointA="淄博",
                    pointB="青岛",
                    trains=[
                        LineTrainInfo(id="K101", delay="30", derection=TrainDirection.DOWN)
                    ]
                )
            ],
            [
                LineSegment(
                    pointA="济南西",
                    pointB="聊城",
                    trains=[]
                ),
                LineSegment(
                    pointA="聊城",
                    pointB="菏泽",
                    trains=[
                        LineTrainInfo(id="K201", delay="30", derection=TrainDirection.DOWN)
                    ]
                )
            ]
        ]
    )
    
    # 构造并返回预测响应
    return PredictResponse(
        event_graph=event_graph,
        statistics=statistics,
        train_table=train_table,
        affect_graph=affect_graph
    )