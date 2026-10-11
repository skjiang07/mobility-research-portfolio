"""Original research excerpts: sequence dataset, padding, Transformer and loss.
Source: MIT_Stay_algorithm-AllUsers.ipynb, code cells 47, 49, 50 (zero-based).
Function/class bodies are preserved. Imports are explicit; no training state or data.
"""
import math
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class GPSSequenceDataset(Dataset):
    def __init__(
        self,
        df,
        feature_cols,
        user_col="user_id",
        time_col="tracked_at",
        label_col="y",
        chunk_len=512,
        stride=512,
    ):
        self.samples = []

        df = df.sort_values([user_col, time_col]).copy()

        for user_id, sub in df.groupby(user_col, sort=False):
            X = sub[feature_cols].to_numpy(dtype="float32")
            y = sub[label_col].to_numpy(dtype="int64")
            times = sub[time_col].to_numpy()
            row_idx = sub.index.to_numpy()

            n = len(sub)

            for start in range(0, n, stride):
                end = min(start + chunk_len, n)

                self.samples.append({
                    "user_id": user_id,
                    "X": X[start:end],
                    "y": y[start:end],
                    "tracked_at": times[start:end],
                    "row_idx": row_idx[start:end],
                })

                if end == n:
                    break

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item = self.samples[idx]

        return {
            "user_id": item["user_id"],
            "X": torch.tensor(item["X"], dtype=torch.float32),
            "y": torch.tensor(item["y"], dtype=torch.long),
            "tracked_at": item["tracked_at"],
            "row_idx": item["row_idx"],
        }


def collate_gps_batch(batch):
    batch_size = len(batch)
    max_len = max(item["X"].shape[0] for item in batch)
    n_features = batch[0]["X"].shape[1]

    X_pad = torch.zeros(batch_size, max_len, n_features, dtype=torch.float32)
    y_pad = torch.zeros(batch_size, max_len, dtype=torch.long)
    mask = torch.zeros(batch_size, max_len, dtype=torch.bool)

    user_ids = []
    tracked_ats = []
    row_idxs = []

    for i, item in enumerate(batch):
        seq_len = item["X"].shape[0]

        X_pad[i, :seq_len] = item["X"]
        y_pad[i, :seq_len] = item["y"]
        mask[i, :seq_len] = True

        user_ids.append(item["user_id"])
        tracked_ats.append(item["tracked_at"])
        row_idxs.append(item["row_idx"])

    return {
        "X": X_pad,
        "y": y_pad,
        "mask": mask,
        "user_id": user_ids,
        "tracked_at": tracked_ats,
        "row_idx": row_idxs,
    }


class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()

        div_term = torch.exp(
            torch.arange(0, d_model, 2).float()
            * (-math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        pe = pe.unsqueeze(0)
        self.register_buffer("pe", pe)

    def forward(self, x):
        seq_len = x.size(1)
        x = x + self.pe[:, :seq_len]
        return self.dropout(x)


class TransformerStayClassifier(nn.Module):
    def __init__(
        self,
        n_features,
        d_model=128,
        nhead=4,
        num_layers=2,
        dim_feedforward=256,
        dropout=0.1,
        num_classes=2,
        max_len=2048,
    ):
        super().__init__()

        self.input_proj = nn.Linear(n_features, d_model)
        self.pos_encoder = PositionalEncoding(
            d_model=d_model,
            max_len=max_len,
            dropout=dropout,
        )

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )

        self.encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers,
        )

        self.classifier = nn.Linear(d_model, num_classes)

    def forward(self, X, mask):
        x = self.input_proj(X)
        x = self.pos_encoder(x)

        src_key_padding_mask = ~mask

        h = self.encoder(
            x,
            src_key_padding_mask=src_key_padding_mask,
        )

        logits = self.classifier(h)
        return logits


def masked_cross_entropy_loss(logits, y, mask, class_weights=None):
    logits_flat = logits[mask]
    y_flat = y[mask]

    return nn.functional.cross_entropy(
        logits_flat,
        y_flat,
        weight=class_weights,
    )
