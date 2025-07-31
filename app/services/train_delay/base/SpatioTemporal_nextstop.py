import torch
import torch.nn as nn
import torch.nn.functional as F
from app.services.train_delay.base import GeoConv
import numpy as np
from torch.autograd import Variable

class Net(nn.Module):
    """
    模块功能: 局部编码器 (Local Encoder)
    负责处理T-1步的历史时序轨迹信息.
    
    设计思路:
    1. 使用GeoConv提取每个滑动窗口的局部空间特征.
    2. 使用RNN (LSTM) 进一步捕捉轨迹的时间动态依赖.
    
    输入:
    - traj (dict): 包含T-1步轨迹序列的字典 (e.g., 'lngs', 'lats', etc.).
    - config (dict): 全局配置字典.
    
    输出:
    - H_local (torch.Tensor): 历史轨迹的编码表示序列. 形状 (B, S, rnn_hidden_size).
                               这是后续注意力机制的Key和Value.
    - lens (list): 每个序列经过卷积后的实际长度 S (S = T-1-ksz+1).
    """
    def __init__(self, kernel_size=3, num_filter=32, rnn='lstm'):
        super(Net, self).__init__()

        self.kernel_size = kernel_size
        self.num_filter = num_filter

        # 1. 地理卷积层, 提取局部空间关系
        #   - 输入: 原始轨迹序列 (T-1 步)
        #   - 输出: 经过1D卷积后的序列 (T-1-ksz+1 步)
        self.geo_conv = GeoConv.Net(kernel_size=kernel_size, num_filter=num_filter)

        # 2. RNN层, 提取时间动态
        #    RNN的输入维度只由GeoConv的输出决定 (num_filter + 1 for dist_gap)
        rnn_input_size = num_filter + 1
        if rnn == 'lstm':
            self.rnn = nn.LSTM(input_size=rnn_input_size,
                               hidden_size=128,
                               num_layers=2,
                               batch_first=True)
        elif rnn == 'rnn':
            self.rnn = nn.RNN(input_size=rnn_input_size,
                              hidden_size=128,
                              num_layers=1,
                              batch_first=True)

    def out_size(self):
        """返回RNN隐藏层的大小, 即H_local中每个向量的维度."""
        return 128

    def forward(self, traj, config):
        """
        前向传播函数.
        """
        # --- 修复 lens 类型 ---
        lens = traj['lens']
        if isinstance(lens, map):
            lens = list(lens)
        # --- 步骤 1: 通过GeoConv提取空间特征 ---
        # conv_locs shape: (B, T-1-ksz+1, num_filter+1)
        conv_locs = self.geo_conv(traj, config)

        # --- 步骤 2: 准备RNN输入 ---
        # 计算经过卷积后的每个序列的实际长度
        lens_conv = [l - self.kernel_size + 1 for l in lens]
        
        # 过滤掉长度小于等于0的无效序列, 避免pack_padded_sequence报错
        valid_indices = [i for i, l in enumerate(lens_conv) if l > 0]
        if not valid_indices:
            # 如果没有有效序列, 返回一个形状正确但内容为空的零张量
            return torch.zeros(len(lens), 0, self.out_size()).to(conv_locs.device), lens_conv

        # 只对有效的序列进行RNN处理
        conv_locs_valid = conv_locs[valid_indices]
        lens_valid = [lens_conv[i] for i in valid_indices]

        # 打包变长序列, 这是处理RNN中padding的最高效方法
        packed_inputs = nn.utils.rnn.pack_padded_sequence(conv_locs_valid, lens_valid, batch_first=True, enforce_sorted=False)

        # --- 步骤 3: 通过RNN处理时间动态 ---
        packed_hiddens, (h_n, c_n) = self.rnn(packed_inputs)

        # --- 步骤 4: 解包序列, 得到最终的历史表示 H_local ---
        # pad_packed_sequence 会将序列恢复到其在该batch中的最大长度
        hiddens, _ = nn.utils.rnn.pad_packed_sequence(packed_hiddens, batch_first=True)
        
        # 创建一个全零张量以恢复原始的batch size, 保证与输入对齐
        # 无效序列的位置将保持为零
        h_local = torch.zeros(len(lens), hiddens.size(1), hiddens.size(2)).to(hiddens.device)
        h_local[valid_indices] = hiddens
        
        return h_local, lens_conv 