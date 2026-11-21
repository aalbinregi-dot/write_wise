"""
BiLSTM + Attention + Linguistic Features — Proposed Essay Scoring Model
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset


# ─── Dataset ──────────────────────────────────────────────────────────────────

class EssayDataset(Dataset):
    def __init__(self, texts, scores, features, vocab, max_len=512):
        self.texts    = texts
        self.scores   = scores
        self.features = features
        self.vocab    = vocab
        self.max_len  = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        tokens = self.texts[idx].lower().split()[:self.max_len]
        ids    = [self.vocab.get(t, self.vocab.get('<UNK>', 1)) for t in tokens]
        # Pad or truncate
        if len(ids) < self.max_len:
            ids += [0] * (self.max_len - len(ids))
        mask  = [1 if i > 0 else 0 for i in ids]

        return {
            'input_ids':  torch.tensor(ids,  dtype=torch.long),
            'mask':       torch.tensor(mask, dtype=torch.float),
            'features':   torch.tensor(self.features[idx], dtype=torch.float),
            'score':      torch.tensor(self.scores[idx], dtype=torch.float),
        }


# ─── Attention Layer ──────────────────────────────────────────────────────────

class SelfAttention(nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        self.attention = nn.Linear(hidden_size * 2, 1)

    def forward(self, lstm_out, mask):
        # lstm_out: (batch, seq, hidden*2)
        attn_scores = self.attention(lstm_out).squeeze(-1)   # (batch, seq)
        # Mask padding positions
        attn_scores = attn_scores.masked_fill(mask == 0, -1e9)
        attn_weights = F.softmax(attn_scores, dim=-1)        # (batch, seq)
        context = torch.bmm(attn_weights.unsqueeze(1), lstm_out).squeeze(1)  # (batch, hidden*2)
        return context, attn_weights


# ─── BiLSTM + Attention + Features Model ─────────────────────────────────────

class BiLSTMAttentionModel(nn.Module):
    def __init__(self, vocab_size, embed_dim=128, hidden_size=128,
                 num_layers=2, feature_dim=20, dropout=0.3):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm      = nn.LSTM(embed_dim, hidden_size, num_layers=num_layers,
                                 batch_first=True, bidirectional=True,
                                 dropout=dropout if num_layers > 1 else 0)
        self.attention = SelfAttention(hidden_size)
        self.dropout   = nn.Dropout(dropout)

        # Feature fusion
        lstm_out_dim = hidden_size * 2
        fused_dim    = lstm_out_dim + feature_dim

        self.fc1 = nn.Linear(fused_dim, 256)
        self.fc2 = nn.Linear(256, 64)
        self.fc3 = nn.Linear(64, 1)
        self.relu = nn.ReLU()
        self.bn1  = nn.BatchNorm1d(256)
        self.bn2  = nn.BatchNorm1d(64)

    def forward(self, input_ids, mask, features):
        # Embedding + LSTM
        emb     = self.dropout(self.embedding(input_ids))       # (B, seq, embed)
        lstm_out, _ = self.lstm(emb)                             # (B, seq, H*2)
        lstm_out = self.dropout(lstm_out)

        # Attention pooling
        context, attn_weights = self.attention(lstm_out, mask)  # (B, H*2)

        # Feature fusion
        fused = torch.cat([context, features], dim=-1)          # (B, H*2+feat)

        # Dense head
        x = self.relu(self.bn1(self.fc1(fused)))
        x = self.dropout(x)
        x = self.relu(self.bn2(self.fc2(x)))
        x = self.dropout(x)
        score = self.fc3(x).squeeze(-1)                          # (B,)
        return score, attn_weights


# ─── Simpler variants for baselines ──────────────────────────────────────────

class LSTMModel(nn.Module):
    """Baseline 2: simple LSTM"""
    def __init__(self, vocab_size, embed_dim=128, hidden_size=128,
                 num_layers=1, dropout=0.3):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm      = nn.LSTM(embed_dim, hidden_size, num_layers=num_layers,
                                 batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.dropout   = nn.Dropout(dropout)
        self.fc        = nn.Linear(hidden_size, 1)

    def forward(self, input_ids, mask=None, features=None):
        emb = self.dropout(self.embedding(input_ids))
        _, (hn, _) = self.lstm(emb)
        out = self.fc(self.dropout(hn[-1]))
        return out.squeeze(-1), None


class BiLSTMNoFeatureModel(nn.Module):
    """Baseline 3: BiLSTM + Attention without linguistic features"""
    def __init__(self, vocab_size, embed_dim=128, hidden_size=128,
                 num_layers=2, dropout=0.3):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm      = nn.LSTM(embed_dim, hidden_size, num_layers=num_layers,
                                 batch_first=True, bidirectional=True,
                                 dropout=dropout if num_layers > 1 else 0)
        self.attention = SelfAttention(hidden_size)
        self.dropout   = nn.Dropout(dropout)
        self.fc1 = nn.Linear(hidden_size * 2, 64)
        self.fc2 = nn.Linear(64, 1)
        self.relu = nn.ReLU()

    def forward(self, input_ids, mask, features=None):
        emb      = self.dropout(self.embedding(input_ids))
        lstm_out, _ = self.lstm(emb)
        context, attn = self.attention(lstm_out, mask)
        x = self.relu(self.fc1(self.dropout(context)))
        out = self.fc2(x).squeeze(-1)
        return out, attn
