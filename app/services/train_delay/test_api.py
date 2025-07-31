from predict_delay_api import predict_delay
import json
from datetime import datetime
from station_utils import get_station_name_by_coords
import pymysql

# 连接数据库
conn = pymysql.connect(host='localhost', user='root', password='qwe123', database='train', charset='utf8')

def get_status(delay, thresholds=[10, 5, 2]):
    if delay >= thresholds[0]:
        return "重大"
    elif delay >= thresholds[1]:
        return "较大"
    elif delay >= thresholds[2]:
        return "一般"
    else:
        return "正常"

def get_train_no_by_driverID(driverID, conn):
    with conn.cursor() as cursor:
        sql = "SELECT train_no FROM train_number WHERE code = %s LIMIT 1"
        cursor.execute(sql, (driverID,))
        row = cursor.fetchone()
        if row:
            return row[0]
        else:
            print(f"[WARNING] driverID {driverID} not found in train_number table!")
            return f"UNKNOWN_{driverID}"

# 读取测试数据集
input_file = 'data/processed_sequences_v1.jsonl'
data = []
missing_driverid = []
with open(input_file, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if line.strip():
            d = json.loads(line)
            driverID = d.get("driverID", -1)
            if driverID == -1:
                missing_driverid.append({"idx": idx, "data": d})
            data.append(d)


# 预测
preds = predict_delay(data)

# 打印每条预测详细信息
max_output = 10
for idx, d in enumerate(data):
    if idx >= max_output:
        break
    start_name = get_station_name_by_coords(d["lngs"][0], d["lats"][0], conn)
    end_name = get_station_name_by_coords(d["lngs"][-1], d["lats"][-1], conn)
    next_name = get_station_name_by_coords(d["lngs"][1], d["lats"][1], conn) if len(d["lngs"]) > 1 else None
    driverID = d.get("driverID", -1)
    train_no = get_train_no_by_driverID(driverID, conn)
    output = {
        "列车车次": train_no,
        "始发站": start_name,
        "终点站": end_name,
        "下一站": next_name,
        "状态": get_status(preds[idx]),
        "影响时长": f"{preds[idx]}分钟"
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

# 统计信息输出
thresholds = [10, 5, 2]
major = sum(p >= thresholds[0] for p in preds)
moderate = sum((p >= thresholds[1]) and (p < thresholds[0]) for p in preds)
minor = sum((p >= thresholds[2]) and (p < thresholds[1]) for p in preds)
stats = {
    "预计影响时长": f"{max(preds)}分钟",
    "预计列车数": len(preds),
    "重大影响列车": major,
    "较大影响列车": moderate,
    "一般影响列车": minor
}
print(json.dumps(stats, ensure_ascii=False, indent=2))

# 关闭数据库连接
conn.close()