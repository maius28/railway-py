import torch
import json
import os
from app.services.train_delay import utils
from app.services.train_delay.data_loader import collate_fn
from app.services.train_delay import models
import inspect

# 用绝对路径加载模型和配置
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config_update.json')
WEIGHT_PATH = os.path.join(os.path.dirname(__file__), 'saved_weights', 'run_log_GPU_2025-06-26_222529.890974_update1003')

config = json.load(open(CONFIG_PATH, 'r'))

# 只保留模型__init__需要的参数
model_init_args = inspect.getfullargspec(models.DeepTTE_nextstop.Net.__init__).args
if 'self' in model_init_args:
    model_init_args.remove('self')
filtered_config = {k: v for k, v in config.items() if k in model_init_args}

model = models.DeepTTE_nextstop.Net(**filtered_config)
model.load_state_dict(torch.load(WEIGHT_PATH, map_location='cpu'))
model.eval()

def prepare_input_for_model(input_data):
    """
    输入: dict 或 list[dict]
    输出: attr, traj (均为tensor/Variable)
    """
    if isinstance(input_data, dict):
        batch = [input_data]
    else:
        batch = input_data
    attr, traj = collate_fn(batch)
    device = next(model.parameters()).device  # 获取模型所在设备
    for k, v in attr.items():
        attr[k] = utils.to_var(v)
        if hasattr(attr[k], 'to'):
            attr[k] = attr[k].to(device)
    for k, v in traj.items():
        traj[k] = utils.to_var(v)
        if hasattr(traj[k], 'to'):
            traj[k] = traj[k].to(device)
    return attr, traj

def predict_delay(input_data):
    """
    输入: 一条或多条原始数据（dict或list[dict]）
    输出: 每条的预测晚点时长list
    """
    attr, traj = prepare_input_for_model(input_data)
    with torch.no_grad():
        pred_dict, _ = model.eval_on_batch(attr, traj, config)
    pred = pred_dict['pred']
    if isinstance(pred, torch.Tensor):
        if pred.dim() == 0:
            # 单个标量
            return [float(pred.item())]
        else:
            return [float(p.item()) for p in pred]
    else:
        # 不是tensor，直接返回
        return [float(pred)]

if __name__ == '__main__':
    # 示例用法
    sample = {
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
    result = predict_delay(sample)
    print("预测晚点时长:", result)