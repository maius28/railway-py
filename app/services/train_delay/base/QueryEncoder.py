import torch
import torch.nn as nn
from app.services.train_delay import utils

class Net(nn.Module):
    """
    模块功能: 查询编码器 (Query Encoder)
    负责生成用于全局编码器(注意力机制)的查询(Query)向量.
    
    设计思路:
    它接收目标站点(T)的上下文信息(天气,位置等)以及与历史轨迹的相对距离信息,
    并将这些物理特征编码为一个高维向量, 作为注意力机制的"问题".
    
    输入:
    - attr (dict): 包含静态属性的字典, 我们将从中提取 'dist' (长期距离: 1到T).
    - y_batch (dict): 包含第T步所有属性的字典 (短期上下文和短期距离: T-1到T).
    - config (dict): 全局配置字典, 用于获取归一化参数.

    输出:
    - q_T (torch.Tensor): 生成的查询向量, 形状 (B, out_size).
    """
    # 根据你的要求, 查询向量将由以下连续特征构成:
    # 1. T步的上下文信息 (来自y_batch)
    continuous_features_from_y = ['lngs', 'lats', 'weather', 'wind', 'temperature', 'dist_gap']
    # 2. 整个行程的长期信息 (来自attr)
    continuous_features_from_attr = ['dist']

    def __init__(self):
        super(Net, self).__init__()
        # weather: 24类，wind: 42类，嵌入维度8
        self.weather_emb = nn.Embedding(24, 8)
        self.wind_emb = nn.Embedding(42, 8)
        # 此模块只进行特征拼接和归一化, 不包含可训练的权重(如Embedding), 故build为空.

    def out_size(self):
        """计算并返回输出向量的总维度."""
        # 总维度 = 8(weather) + 8(wind) + 其余连续特征数 + attr特征数
        return 8 + 8 + (len(self.continuous_features_from_y) - 2) + len(self.continuous_features_from_attr)

    def forward(self, attr, y_batch, config):
        """
        前向传播函数.
        """
        processed_features = []
        
        # --- 步骤 1: 处理来自 y_batch 的连续特征 (T步的上下文和短期距离) ---
        for name in self.continuous_features_from_y:
            if name in y_batch:
                if name == 'weather':
                    # weather embedding
                    weather_idx = y_batch[name].long()
                    weather_emb = self.weather_emb(weather_idx)
                    processed_features.append(weather_emb)
                elif name == 'wind':
                    wind_idx = y_batch[name].long()
                    wind_emb = self.wind_emb(wind_idx)
                    processed_features.append(wind_emb)
                else:
                    normalized_val = utils.normalize(y_batch[name], name)
                    processed_features.append(normalized_val.view(-1, 1))
        
        # --- 步骤 2: 处理来自 attr 的连续特征 (长期距离) ---
        for name in self.continuous_features_from_attr:
            if name in attr:
                # 'dist' 在这里代表 1 到 T 的总距离 (长期距离)
                normalized_val = utils.normalize(attr[name], name)
                processed_features.append(normalized_val.view(-1, 1))
        
        # --- 步骤 3: 将所有处理过的特征拼接成最终的查询向量 q_T ---
        if not processed_features:
            # 处理边缘情况: 如果没有任何特征被处理, 返回一个零张量
            batch_size = next(iter(y_batch.values())).size(0)
            return torch.zeros(batch_size, self.out_size()).to(y_batch[next(iter(y_batch.keys()))].device)
            
        return torch.cat(processed_features, dim=1) 