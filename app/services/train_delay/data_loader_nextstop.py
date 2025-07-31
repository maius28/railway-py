import time
import utils
import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

import numpy as np
import ujson as json

class MySet(Dataset):
    def __init__(self, input_file, config):
        """
        数据集初始化
        :param input_file: json格式的输入文件名
        :param config: a dict containing all the configurations, including kernel_size
        """
        self.content = []
        kernel_size = config.get('kernel_size', 3) # 从config获取kernel_size, 默认为3
        # 使用绝对路径
        file_path = os.path.join('D:/项目各文档/6-30-1/DeepTTE_11/data', input_file)
        with open(file_path, 'r') as file:
            for line in file:
                try:
                    # 每行是一个json字符串，代表一条完整的轨迹
                    json_dict = json.loads(line)
                    # 过滤掉对于模型来说过短的轨迹
                    # 历史轨迹长度(T-1) 必须 >= kernel_size.
                    # 因此, 总轨迹长度(T) 必须 >= kernel_size + 1.
                    if len(json_dict.get('lngs', [])) >= kernel_size + 1:
                        self.content.append(json_dict)
                except json.JSONDecodeError as e:
                    print(f"解析JSON时出错: {line}. 错误: {e}")
        # 存储每条轨迹的原始长度
        self.lengths = [len(x['lngs']) for x in self.content]

    def __getitem__(self, idx):
        """
        核心函数：定义如何根据索引idx获取一条数据样本 (x, y)
        """
        item = self.content[idx]
        T = len(item['lngs']) # 获取当前轨迹的总步数 T

        # --- 构造输入 x ---
        # x 是一个字典, 包含了从第 1 步到第 T-1 步的所有历史轨迹信息.
        # 对于 item 中的每个键值对:
        # - 如果值v是一个列表且长度为T (说明是轨迹序列), 则取其前 T-1 个元素.
        # - 否则 (如 driverID 等静态信息), 保持不变.
        x_item = {k: v[:T-1] if isinstance(v, list) and len(v) == T else v for k, v in item.items()}

        # --- 构造标签 y ---
        # y 是一个字典, 包含了目标站点 (第 T 步) 的所有相关属性.
        # 这是 QueryEncoder 和全局损失函数所需要的信息.
        y_item = {}
        for k, v in item.items():
            # 如果值v是一个列表且长度为T, 说明是轨迹序列, 我们取其最后一个元素.
            if isinstance(v, list) and len(v) == T:
                y_item[k] = v[-1]

        return x_item, y_item

    def __len__(self):
        return len(self.content)

def collate_fn(data):
    """
    自定义的批处理函数 (collate_fn):
    将一个批次内的数据样本 (list of (x, y) tuples) 处理成模型需要的张量格式.
    """
    xs, ys = zip(*data)
    stat_attrs = ['dist', 'time']
    info_attrs = ['driverID', 'dateID', 'weekID', 'timeID']
    traj_attrs = ['lngs', 'lats', 'time_gap', 'dist_gap','weather','wind','temperature']

    attr, traj = {}, {}
    lens = np.asarray([len(item['lngs']) for item in xs])

    # 标准化静态属性
    for key in stat_attrs:
        x_vals = [item[key] for item in xs]
        attr[key] = utils.normalize(torch.FloatTensor(x_vals), key)

    # 转换ID类属性为LongTensor
    for key in info_attrs:
        attr[key] = torch.LongTensor([item[key] for item in xs])

    # 对变长的动态轨迹属性进行填充 (Padding)
    for key in traj_attrs:
        seqs = [item[key] for item in xs]
        mask = np.arange(lens.max()) < lens[:, None]
        padded = np.zeros(mask.shape, dtype=np.float32)
        if np.concatenate(seqs).size > 0:
            padded[mask] = np.concatenate(seqs)
        if key in ['weather', 'wind']:
            traj[key] = torch.from_numpy(padded).long()
        elif key in ['lngs', 'lats', 'time_gap', 'dist_gap', 'temperature']:
            padded = utils.normalize(padded, key)
            traj[key] = torch.from_numpy(padded).float()
        else:
            traj[key] = torch.from_numpy(padded).float()
    traj['lens'] = lens.tolist()

    # --- 2. 处理标签 Y (目标站点) ---
    y_batch = {}
    if ys and isinstance(ys[0], dict):
        for key in ys[0].keys():
            values = [item.get(key) for item in ys]
            try:
                if isinstance(values[0], (int, np.integer)):
                    y_batch[key] = torch.LongTensor(values)
                elif isinstance(values[0], (float, np.floating)):
                    y_batch[key] = torch.FloatTensor(values)
                else:
                    y_batch[key] = values
            except (TypeError, ValueError):
                y_batch[key] = values
    # 标签 time_gap 归一化
    if 'time_gap' in y_batch:
        y_batch['time_gap'] = utils.normalize(y_batch['time_gap'], 'time_gap')

    return (attr, traj), y_batch

class BatchSampler:
    def __init__(self, dataset, batch_size):
        self.count = len(dataset)
        self.batch_size = batch_size
        self.lengths = dataset.lengths
        self.indices = list(range(self.count))
    def __iter__(self):
        np.random.shuffle(self.indices)
        chunk_size = self.batch_size * 100
        chunks = (self.count + chunk_size - 1) // chunk_size
        for i in range(chunks):
            partial_indices = self.indices[i * chunk_size: (i + 1) * chunk_size]
            partial_indices.sort(key = lambda x: self.lengths[x], reverse = True)
            self.indices[i * chunk_size: (i + 1) * chunk_size] = partial_indices
        batches = (self.count - 1 + self.batch_size) // self.batch_size
        for i in range(batches):
            yield self.indices[i * self.batch_size: (i + 1) * self.batch_size]
    def __len__(self):
        return (self.count + self.batch_size - 1) // self.batch_size

def get_loader(input_file, batch_size, config, shuffle=True):
    dataset = MySet(input_file = input_file, config=config)
    batch_sampler = BatchSampler(dataset, batch_size)
    data_loader = DataLoader(dataset = dataset, \
                             batch_size = 1, \
                             collate_fn = lambda x: collate_fn(x), \
                             num_workers = 0,
                             batch_sampler = batch_sampler,
                             pin_memory = True
    )
    return data_loader