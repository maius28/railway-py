import time
from app.services.train_delay import utils
import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

import numpy as np
import ujson as json

class MySet(Dataset):
    def __init__(self, input_file, config=None):
        self.content = []
        # 获取脚本所在的目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 从config获取kernel_size，默认为3
        kernel_size = config.get('kernel_size', 3) if config else 3
        min_length = kernel_size + 1  # 原始轨迹长度至少需要 kernel_size + 1

        with open(input_file, 'r') as file:
            for line in file:
                try:
                    json_dict = json.loads(line)
                    # 根据kernel_size过滤轨迹长度
                    # 原始轨迹长度T >= kernel_size + 1
                    # 这样历史轨迹长度(T-1) >= kernel_size，可以进行卷积操作
                    if len(json_dict.get('lngs', [])) >= min_length:
                        self.content.append(json_dict)
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON on line: {line}. Error: {e}")

        self.lengths = [len(x['lngs']) for x in self.content]

        # self.content = open('./data/' + input_file, 'r').readlines()
        # self.content = map(lambda x: json.loads(x), self.content)
        # self.lengths = map(lambda x: len(x['lngs']), self.content)

    def __getitem__(self, idx):
        return self.content[idx]

    def __len__(self):
        return len(self.content)

def collate_fn(data):
    # print("\n\nFunction: ", len(data))
    # print("------------------")
    stat_attrs = ['dist', 'time']
    info_attrs = ['driverID', 'dateID', 'weekID', 'timeID']
    traj_attrs = ['lngs', 'lats', 'states', 'time_gap', 'dist_gap','weather','wind','temperature']

    attr, traj = {}, {}

    lens = np.asarray([len(item['lngs']) for item in data])

    # print("Lens: ", len(lens))

    for key in stat_attrs:
        x = torch.FloatTensor([item[key] for item in data])
        attr[key] = utils.normalize(x, key)

    # print("X: ", x)
    # print("ATRR: ", attr)

    for key in info_attrs:
        attr[key] = torch.LongTensor([item[key] for item in data])

    for key in traj_attrs:
        # pad to the max length
        # print("Over here!")
        # print([len(item[key]) for item in data])
        # seqs = np.asarray(item[key] for item in data)
        # seqs = []
        seqs = [item[key] for item in data]
        # print("FLAG: ", seqs)
        # print("Range: ", np.arange(lens.max()))
        # print("Lens: ", lens)
        # print("Check: ", lens[:, None])
        mask = np.arange(lens.max()) < lens[:, None]
        # print("mask: ", mask)
        padded = np.zeros(mask.shape, dtype = np.float32)
        # seqs = list(seqs)
        padded[mask] = np.concatenate(seqs)
        # print("Array:" , padded)

        if key in ['lngs', 'lats', 'time_gap', 'dist_gap','weather','wind','temperature']:
            padded = utils.normalize(padded, key)

        padded = torch.from_numpy(padded).float()
        traj[key] = padded

    lens = lens.tolist()
    traj['lens'] = lens

    return attr, traj

class BatchSampler:
    def __init__(self, dataset, batch_size):
        self.count = len(dataset)
        # print(batch_size)
        self.batch_size = batch_size
        self.lengths = dataset.lengths
        self.indices = list(range(self.count))
        # print("------------------------------")
        # print(list(self.indices))

    def __iter__(self):
        '''
        Divide the data into chunks with size = batch_size * 100
        sort by the length in one chunk
        '''
        np.random.shuffle(self.indices)

        chunk_size = self.batch_size * 100

        # print("Hello: ", chunk_size)
        # print("K: ", self.count)

        chunks = (self.count + chunk_size - 1) // chunk_size

        # print("Chunks: ", chunks)

        # re-arrange indices to minimize the padding
        for i in range(chunks):
            partial_indices = self.indices[i * chunk_size: (i + 1) * chunk_size]
            partial_indices.sort(key = lambda x: self.lengths[x], reverse = True)
            self.indices[i * chunk_size: (i + 1) * chunk_size] = partial_indices

        # print(len(self.indices))

        # print("Here now")

        # print(self.indices)

        # yield batch
        batches = (self.count - 1 + self.batch_size) // self.batch_size

        # print("Batch Size: ", self.batch_size)
        # print("Batches: ", batches)


        for i in range(batches):
            yield self.indices[i * self.batch_size: (i + 1) * self.batch_size]

    def __len__(self):
        return (self.count + self.batch_size - 1) // self.batch_size

def get_loader(input_file, batch_size, config=None):
    dataset = MySet(input_file=input_file, config=config)

    batch_sampler = BatchSampler(dataset, batch_size)

    data_loader = DataLoader(dataset = dataset, \
                             batch_size = 1, \
                             collate_fn = lambda x: collate_fn(x), \
                             num_workers = 0,
                             batch_sampler = batch_sampler,
                             pin_memory = True
    )

    return data_loader
