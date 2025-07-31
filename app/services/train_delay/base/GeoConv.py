import torch
import torch.nn as nn
import torch.nn.functional as F

from app.services.train_delay import utils
import numpy as np

from torch.autograd import Variable

class Net(nn.Module):
    def __init__(self, kernel_size, num_filter):
        super(Net, self).__init__()

        self.kernel_size = kernel_size
        self.num_filter = num_filter

        self.build()

    def build(self):
        # weather: 24类，wind: 42类，嵌入维度8
        self.weather_emb = nn.Embedding(24, 8)
        self.wind_emb = nn.Embedding(42, 8)
        # 2(lng,lat)+8(weather)+8(wind)+1(temperature) = 19
        self.process_coords = nn.Linear(19, 16)
        self.conv = nn.Conv1d(16, self.num_filter, self.kernel_size)

    def forward(self, traj, config):
        lngs = torch.unsqueeze(traj['lngs'], dim = 2)
        lats = torch.unsqueeze(traj['lats'], dim = 2)
        # weather/wind 先转 long 再 embed
        weather = traj['weather'].long()
        wind = traj['wind'].long()
        
        # shape: (B, T, 8)
        weather_emb = self.weather_emb(weather)
        wind_emb = self.wind_emb(wind)
        temperature = traj['temperature']
        if temperature.dim() == 2:
            temperature = torch.unsqueeze(temperature, dim=2)
        
        # 拼接: lngs, lats, weather_emb, wind_emb, temperature
        locs = torch.cat((lngs, lats, weather_emb, wind_emb, temperature), dim=2)
          
        # map the coords into 16-dim vector
        locs = torch.tanh(self.process_coords(locs))
        locs = locs.permute(0, 2, 1)

        conv_locs = F.elu(self.conv(locs)).permute(0, 2, 1)

        # calculate the dist for local paths
        local_dist = utils.get_local_seq(traj['dist_gap'], self.kernel_size, config['dist_gap_mean'], config['dist_gap_std'])
        local_dist = torch.unsqueeze(local_dist, dim = 2)

        conv_locs = torch.cat((conv_locs, local_dist), dim = 2)

        return conv_locs

