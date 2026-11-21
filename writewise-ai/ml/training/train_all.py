"""
Training Script — All Models
Trains TF-IDF+DNN, LSTM, BiLSTM, BiLSTM+Attention+Features.
Compares results and saves best checkpoint.
"""
import os
import sys
import json
import time
import logging
import pickle
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPRegressor

# Add project to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.preprocessing.data_loader import load_asap2, split_asap2
from ml.features.linguistic_features import extract_features, get_feature_vector
from ml.models.bilstm_attention.model import (
    BiLSTMAttentionModel, BiLSTMNoFeatureModel, LSTMModel, EssayDataset
)
from ml.evaluation.metrics import compute_all_metrics, print_metrics_table

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

CHECKPOINTS_DIR = PROJECT_ROOT / 'ml' / 'checkpoints'
CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR   = PROJECT_ROOT / 'datasets' / 'processed'


DEVICE   = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
SEED     = 42
MAX_LEN  = 300
BATCH    = 32
EPOCHS   = 20
LR       = 1e-3
FEAT_DIM = 20


def set_seed(seed=SEED):
    np.random.seed(seed)
    torch.manual_seed(seed)


def build_vocab(texts, max_vocab=15000):
    counter = Counter()
    for t in texts:
        counter.update(t.lower().split())
    vocab = {'<PAD>': 0, '<UNK>': 1}
    for word, _ in counter.most_common(max_vocab - 2):
        vocab[word] = len(vocab)
    return vocab


def compute_features(texts):
    logger.info('Extracting linguistic features...')
    feats = []
    for t in texts:
        f = extract_features(t)
        feats.append(get_feature_vector(f))
    return np.array(feats, dtype=np.float32)


def normalize_features(train_feats, val_feats, test_feats):
    mean = train_feats.mean(axis=0)
    std  = train_feats.std(axis=0) + 1e-8
    return ((train_feats - mean) / std,
            (val_feats  - mean) / std,
            (test_feats - mean) / std,
            mean, std)


# ─── TF-IDF + MLP (Baseline 1) ───────────────────────────────────────────────

def train_tfidf_mlp(train_df, val_df, test_df):
    logger.info('Training TF-IDF + MLP (Baseline 1)...')
    tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), min_df=1)

    X_train = tfidf.fit_transform(train_df['essay_text']).toarray()
    X_val   = tfidf.transform(val_df['essay_text']).toarray()
    X_test  = tfidf.transform(test_df['essay_text']).toarray()

    y_train = train_df['score_normalized'].values
    y_val   = val_df['score_normalized'].values
    y_test  = test_df['score_normalized'].values

    mlp = MLPRegressor(hidden_layer_sizes=(256, 128, 64), activation='relu',
                       max_iter=200, early_stopping=True, validation_fraction=0.1,
                       random_state=SEED, verbose=False)
    mlp.fit(X_train, y_train)

    y_pred = np.clip(mlp.predict(X_test), 1, 6)
    metrics = compute_all_metrics(y_test, y_pred)

    # Save
    with open(CHECKPOINTS_DIR / 'tfidf_mlp.pkl', 'wb') as f:
        pickle.dump({'tfidf': tfidf, 'mlp': mlp}, f)
    with open(CHECKPOINTS_DIR / 'tfidf_mlp_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f'TF-IDF+MLP → QWK={metrics["qwk"]:.4f} MAE={metrics["mae"]:.4f}')
    return metrics


# ─── PyTorch training loop ────────────────────────────────────────────────────

def train_epoch(model, loader, optimizer, criterion):
    model.train()
    total_loss = 0
    for batch in loader:
        ids   = batch['input_ids'].to(DEVICE)
        mask  = batch['mask'].to(DEVICE)
        feats = batch['features'].to(DEVICE)
        y     = batch['score'].to(DEVICE)

        optimizer.zero_grad()
        pred, _ = model(ids, mask, feats)
        loss = criterion(pred, y)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        total_loss += loss.item()
    return total_loss / len(loader)


def eval_epoch(model, loader):
    model.eval()
    all_preds, all_true = [], []
    with torch.no_grad():
        for batch in loader:
            ids   = batch['input_ids'].to(DEVICE)
            mask  = batch['mask'].to(DEVICE)
            feats = batch['features'].to(DEVICE)
            y     = batch['score'].cpu().numpy()
            pred, _ = model(ids, mask, feats)
            all_preds.extend(pred.cpu().numpy())
            all_true.extend(y)
    return np.array(all_true), np.clip(np.array(all_preds), 1, 6)


def train_pytorch_model(model_class, model_name, train_ds, val_ds, test_ds,
                        vocab_size, extra_kwargs=None):
    logger.info(f'Training {model_name}...')
    kwargs = {'vocab_size': vocab_size, 'embed_dim': 128, 'hidden_size': 128,
              'num_layers': 2, 'dropout': 0.3}
    if extra_kwargs:
        kwargs.update(extra_kwargs)

    model = model_class(**kwargs).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)
    criterion = nn.MSELoss()

    train_loader = DataLoader(train_ds, batch_size=BATCH, shuffle=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH)

    best_qwk    = -1
    best_path   = CHECKPOINTS_DIR / f'{model_name}.pt'
    patience    = 5
    wait        = 0

    for epoch in range(1, EPOCHS + 1):
        train_loss = train_epoch(model, train_loader, optimizer, criterion)
        y_true, y_pred = eval_epoch(model, val_loader)
        val_metrics = compute_all_metrics(y_true, y_pred)
        scheduler.step(val_metrics['mae'])

        logger.info(f'[{model_name}] Epoch {epoch:02d} loss={train_loss:.4f} '
                    f'val_qwk={val_metrics["qwk"]:.4f} val_mae={val_metrics["mae"]:.4f}')

        if val_metrics['qwk'] > best_qwk:
            best_qwk = val_metrics['qwk']
            torch.save(model.state_dict(), best_path)
            wait = 0
        else:
            wait += 1
            if wait >= patience:
                logger.info(f'Early stopping at epoch {epoch}')
                break

    # Test evaluation
    model.load_state_dict(torch.load(best_path))
    y_true, y_pred = eval_epoch(model, test_loader)
    test_metrics = compute_all_metrics(y_true, y_pred)

    with open(CHECKPOINTS_DIR / f'{model_name}_metrics.json', 'w') as f:
        json.dump(test_metrics, f, indent=2)

    logger.info(f'{model_name} test → QWK={test_metrics["qwk"]:.4f} MAE={test_metrics["mae"]:.4f}')
    return test_metrics


def main():
    set_seed()
    logger.info(f'Device: {DEVICE}')

    # Load data
    logger.info('Loading ASAP2 dataset...')
    processed_train = PROCESSED_DIR / 'train.csv'
    processed_val   = PROCESSED_DIR / 'val.csv'
    processed_test  = PROCESSED_DIR / 'test.csv'

    if processed_train.exists() and processed_val.exists() and processed_test.exists():
        logger.info('Loading processed splits from datasets/processed/...')
        train_df = pd.read_csv(processed_train)
        val_df   = pd.read_csv(processed_val)
        test_df  = pd.read_csv(processed_test)
    else:
        df = load_asap2()
        train_df, val_df, test_df = split_asap2(df)

    # Limit for CPU training
    sample_size = min(500, len(train_df))
    train_df = train_df.sample(n=sample_size, random_state=SEED).reset_index(drop=True)
    val_df   = val_df.sample(n=min(100, len(val_df)), random_state=SEED).reset_index(drop=True)
    test_df  = test_df.sample(n=min(100, len(test_df)), random_state=SEED).reset_index(drop=True)
    logger.info(f'Using {len(train_df)} training, {len(val_df)} val, {len(test_df)} test samples')


    # Vocabulary
    vocab = build_vocab(train_df['essay_text'].tolist())
    with open(CHECKPOINTS_DIR / 'vocab.pkl', 'wb') as f:
        pickle.dump(vocab, f)
    vocab_size = len(vocab)
    logger.info(f'Vocab size: {vocab_size}')

    # Linguistic features
    train_feats = compute_features(train_df['essay_text'].tolist())
    val_feats   = compute_features(val_df['essay_text'].tolist())
    test_feats  = compute_features(test_df['essay_text'].tolist())
    train_feats, val_feats, test_feats, feat_mean, feat_std = normalize_features(
        train_feats, val_feats, test_feats)

    feat_info = {'mean': feat_mean.tolist(), 'std': feat_std.tolist()}
    with open(CHECKPOINTS_DIR / 'feature_stats.json', 'w') as f:
        json.dump(feat_info, f)

    # Datasets
    def make_ds(df, feats):
        return EssayDataset(
            texts=df['essay_text'].tolist(),
            scores=df['score_normalized'].tolist(),
            features=feats,
            vocab=vocab,
            max_len=MAX_LEN,
        )

    train_ds = make_ds(train_df, train_feats)
    val_ds   = make_ds(val_df,   val_feats)
    test_ds  = make_ds(test_df,  test_feats)

    all_results = {}

    # Baseline 1: TF-IDF + MLP
    all_results['TF-IDF + MLP'] = train_tfidf_mlp(train_df, val_df, test_df)

    # Baseline 2: LSTM
    all_results['LSTM'] = train_pytorch_model(
        LSTMModel, 'lstm', train_ds, val_ds, test_ds, vocab_size,
        extra_kwargs={'num_layers': 1}
    )

    # Baseline 3: BiLSTM + Attention (no features)
    all_results['BiLSTM + Attention'] = train_pytorch_model(
        BiLSTMNoFeatureModel, 'bilstm_attention', train_ds, val_ds, test_ds, vocab_size
    )

    # Proposed: BiLSTM + Attention + Features
    all_results['BiLSTM + Attn + Features (Proposed)'] = train_pytorch_model(
        BiLSTMAttentionModel, 'bilstm_attention_features', train_ds, val_ds, test_ds,
        vocab_size, extra_kwargs={'feature_dim': FEAT_DIM}
    )

    # Summary
    print_metrics_table(all_results)

    with open(CHECKPOINTS_DIR / 'all_results.json', 'w') as f:
        json.dump(all_results, f, indent=2)

    logger.info('✅ Training complete. Results saved.')


if __name__ == '__main__':
    main()
