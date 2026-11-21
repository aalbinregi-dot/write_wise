"""
Inference Pipeline — loads trained model, scores essays, extracts all features
"""
import json
import pickle
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

PROJECT_ROOT    = Path(__file__).resolve().parent.parent.parent
CHECKPOINTS_DIR = PROJECT_ROOT / 'ml' / 'checkpoints'

_cache = {}


def _load_resources():
    """Lazy-load model and vocab into memory cache."""
    if _cache:
        return _cache

    try:
        import torch
        from ml.models.bilstm_attention.model import BiLSTMAttentionModel, EssayDataset

        vocab_path = CHECKPOINTS_DIR / 'vocab.pkl'
        model_path = CHECKPOINTS_DIR / 'bilstm_attention_features.pt'
        stats_path = CHECKPOINTS_DIR / 'feature_stats.json'

        if not (vocab_path.exists() and model_path.exists()):
            logger.warning('Model not trained yet — using rule-based fallback scorer')
            _cache['mode'] = 'fallback'
            return _cache

        with open(vocab_path, 'rb') as f:
            vocab = pickle.load(f)
        with open(stats_path) as f:
            stats = json.load(f)

        model = BiLSTMAttentionModel(
            vocab_size=len(vocab), embed_dim=128, hidden_size=128,
            num_layers=2, dropout=0.0, feature_dim=20
        )
        model.load_state_dict(torch.load(model_path, map_location='cpu'))
        model.eval()

        _cache.update({'mode': 'model', 'model': model, 'vocab': vocab,
                       'feat_mean': np.array(stats['mean']),
                       'feat_std':  np.array(stats['std'])})
    except Exception as e:
        logger.error(f'Model load error: {e}')
        _cache['mode'] = 'fallback'

    return _cache


def score_essay(text: str) -> dict:
    """
    Score an essay text. Returns:
      { score, confidence, model_version, features }
    """
    from ml.features.linguistic_features import extract_features, get_feature_vector

    features = extract_features(text)
    feat_vec = get_feature_vector(features)

    resources = _load_resources()

    if resources.get('mode') == 'fallback':
        score = _fallback_score(features)
        confidence = 0.60
    else:
        score, confidence = _model_score(text, feat_vec, resources)

    return {
        'score':         round(float(np.clip(score, 1.0, 6.0)), 2),
        'confidence':    round(float(confidence), 3),
        'model_version': '1.0.0',
        'features':      features,
    }


def _model_score(text, feat_vec, resources):
    import torch

    vocab = resources['vocab']
    model = resources['model']
    mean  = resources['feat_mean']
    std   = resources['feat_std']

    tokens = text.lower().split()[:300]
    ids    = [vocab.get(t, vocab.get('<UNK>', 1)) for t in tokens]
    if len(ids) < 300:
        ids += [0] * (300 - len(ids))
    mask = [1 if i > 0 else 0 for i in ids]

    feat_norm = (np.array(feat_vec) - mean) / (std + 1e-8)

    with torch.no_grad():
        inp  = torch.tensor([ids],      dtype=torch.long)
        msk  = torch.tensor([mask],     dtype=torch.float)
        feat = torch.tensor([feat_norm], dtype=torch.float)
        score, _ = model(inp, msk, feat)

    return float(score.item()), 0.85


def _fallback_score(features: dict) -> float:
    """
    Rule-based heuristic score when model not yet trained.
    Combines readability, vocabulary, and length signals.
    """
    wc        = min(features.get('word_count', 0) / 400, 1.0)
    ttr       = min(features.get('type_token_ratio', 0) * 2, 1.0)
    read_ease = features.get('flesch_reading_ease', 50)
    readability = max(0, min((read_ease - 20) / 60, 1.0))
    academic  = min(features.get('academic_word_ratio', 0) * 20, 1.0)
    structure = (features.get('has_introduction', 0) + features.get('has_conclusion', 0)) / 2

    score = 1 + (wc * 1.2 + ttr * 1.0 + readability * 0.8 + academic * 0.7 + structure * 0.8) * (5 / (1.2+1+0.8+0.7+0.8))
    return float(np.clip(score, 1.0, 6.0))
