import torch
import torch.nn as nn
import torch.nn.functional as F
from app.services.train_delay import utils
from app.services.train_delay.base import GeoConv
from app.services.train_delay.base import SpatioTemporal_nextstop as SpatioTemporal
from app.services.train_delay.base import QueryEncoder
import numpy as np
from torch.autograd import Variable
import sys
import os


class DotProductAttention(nn.Module):
    """
    Standard Dot-Product Attention module.
    Computes attention scores between a query and a set of keys,
    and returns the weighted sum of values.
    """
    def forward(self, query, key, value, mask=None):
        """
        Args:
            query (Tensor): Query tensor, shape (B, F).
            key (Tensor): Key tensor, shape (B, S, F).
            value (Tensor): Value tensor, shape (B, S, F).
            mask (Tensor): Boolean mask for padding, shape (B, S).
        """

        score = torch.bmm(key, query.unsqueeze(2)).squeeze(2)  # (B, S)

        if mask is not None:
            score.masked_fill_(~mask, -float('inf'))

        attn_weights = F.softmax(score, dim=1)  # (B, S)
        
        # Weighted sum of values
        context = torch.bmm(value.transpose(1, 2), attn_weights.unsqueeze(2)).squeeze(2) # (B, F)
        
        return context, attn_weights



class GlobalDecoder(nn.Module):
    def __init__(self, input_size, num_final_fcs, hidden_size=128):
        super(GlobalDecoder, self).__init__()
        self.mlp = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1)
        )

    def forward(self, z_global):
        return self.mlp(z_global)

    def eval_on_batch(self, pred, label, mean, std):
        if not isinstance(label, torch.Tensor):
            label = torch.tensor(label, dtype=torch.float32)
        if not isinstance(pred, torch.Tensor):
            pred = torch.tensor(pred, dtype=torch.float32)
        
        label_denorm = label * std + mean
        pred_denorm = pred * std + mean
        
        mae = torch.mean(torch.abs(pred_denorm - label_denorm))
        rmse = torch.sqrt(torch.mean((pred_denorm - label_denorm) ** 2))
        mse = torch.mean((pred_denorm - label_denorm) ** 2)
        return {
            'pred': pred_denorm.squeeze(),
            'label': label_denorm.squeeze(),
            'mae': mae.item(),
            'rmse': rmse.item(),
            'mse': mse.item()
        }

class LocalDecoder(nn.Module):
    def __init__(self, input_size, hidden_size=64):
        super(LocalDecoder, self).__init__()
        self.mlp = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 1)
        )

    def forward(self, packed_h_local, traj, local_lens_valid, config):
        # Prediction part is unchanged
        delta_y_hat = self.mlp(packed_h_local.data).squeeze(-1)
        

        time_gap_padded = traj['time_gap']
        k_size = config.get('kernel_size', 3)

        seq_len = time_gap_padded.size(1)
        if seq_len < k_size:
            delta_y_label_padded = torch.zeros(time_gap_padded.size(0), 0, device=time_gap_padded.device)
        else:
            indices = torch.arange(seq_len, device=time_gap_padded.device)
            first_seq = torch.index_select(time_gap_padded, dim=1, index=indices[k_size - 1:])
            second_seq = torch.index_select(time_gap_padded, dim=1, index=indices[:-k_size + 1])
            delta_y_label_padded = first_seq - second_seq

        # Pack the correctly calculated labels
        packed_labels = nn.utils.rnn.pack_padded_sequence(
            delta_y_label_padded,
            local_lens_valid,
            batch_first=True,
            enforce_sorted=False
        )
        delta_y_label = packed_labels.data
        return delta_y_hat, delta_y_label



class Net(nn.Module):
    def __init__(self, kernel_size=3, num_filter=32,
                 num_final_fcs=3, final_fc_size=128, alpha=0.3):
        super(Net, self).__init__()
        self.kernel_size = kernel_size
        self.alpha = alpha
        self.build(num_filter, num_final_fcs, final_fc_size)
        self.init_weight()
        self.loss_func = nn.L1Loss()

    def build(self, num_filter, num_final_fcs, final_fc_size):
        self.local_encoder = SpatioTemporal.Net(
            kernel_size=self.kernel_size,
            num_filter=num_filter
        )
        local_hidden_size = self.local_encoder.out_size()
        self.query_encoder = QueryEncoder.Net()
        query_size = self.query_encoder.out_size()
        
        # Linear projection for the query
        self.W_q = nn.Linear(query_size, local_hidden_size)
        
        # CHANGE: Instantiate the new Attention module
        self.attention = DotProductAttention()

        self.global_decoder = GlobalDecoder(
            input_size=local_hidden_size,
            num_final_fcs=num_final_fcs,
            hidden_size=final_fc_size
        )
        self.local_decoder = LocalDecoder(input_size=local_hidden_size)

    def init_weight(self):
        for name, param in self.named_parameters():
            if name.find('.bias') != -1:
                param.data.fill_(0)
            elif name.find('.weight') != -1:
                nn.init.xavier_uniform_(param.data)
    
    def forward(self, attr, traj, config):

        traj_history = {}
        y_features = {}
        original_lens = traj['lens']
        
        for k, v in traj.items():
            if k == 'lens':
                traj_history[k] = [l - 1 if l > 0 else 0 for l in original_lens]
            else:
                traj_history[k] = v[:, :-1]
                y_features[k] = v[:, -1]

        # 1. Local Encoder
        H_local, local_lens = self.local_encoder(traj_history, config)

        # 2. Query Encoder
        q_T = self.query_encoder(attr, y_features, config)

        # 3. CHANGE: Attention Mechanism is now a cleaner call
        q_T_proj = self.W_q(q_T)
        mask = torch.arange(H_local.size(1), device=H_local.device)[None, :] < torch.tensor(local_lens, device=H_local.device)[:, None]
        z_global, attn_weights = self.attention(q_T_proj, H_local, H_local, mask=mask)
        
        # 4. Global Decoder
        y_hat_T = self.global_decoder(z_global).squeeze(-1)

        # 5. Local Decoder
        valid_local_indices = [i for i, l in enumerate(local_lens) if l > 0]
        if not valid_local_indices:
            delta_y_hat = torch.tensor([], device=H_local.device)
            delta_y_label = torch.tensor([], device=H_local.device)
        else:
            H_local_valid = H_local[valid_local_indices]
            local_lens_valid = [local_lens[i] for i in valid_local_indices]
            traj_history_valid = {k: v[valid_local_indices] for k, v in traj_history.items() if k != 'lens'}
            
            packed_h_local = nn.utils.rnn.pack_padded_sequence(H_local_valid, local_lens_valid, batch_first=True, enforce_sorted=False)
            delta_y_hat, delta_y_label = self.local_decoder(packed_h_local, traj_history_valid, local_lens_valid, config)
        
        # 6. Extract Global Label
        target_T = y_features['time_gap']
        
        return y_hat_T, (delta_y_hat, delta_y_label), target_T

    def eval_on_batch(self, attr, traj, config):
        y_hat_T, (delta_y_hat, delta_y_label), target_T = self.forward(attr, traj, config)
        
        mean = config['time_gap_mean']
        std = config['time_gap_std']
        pred_dict = self.global_decoder.eval_on_batch(y_hat_T, target_T, mean, std)

        global_loss = self.loss_func(y_hat_T, target_T)

        if delta_y_hat.numel() > 0:
            local_loss = self.loss_func(delta_y_hat, delta_y_label)
        else:
            local_loss = torch.tensor(0.0, device=y_hat_T.device)
            
        loss = (1 - self.alpha) * global_loss + self.alpha * local_loss
        
        return pred_dict, loss 