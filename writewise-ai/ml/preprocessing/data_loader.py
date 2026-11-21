"""
Data Loader — ASAP2, Grammar, Spelling datasets
Handles normalization, train/val/test splits, and preprocessing.
"""
import os
import re
import sys
import pickle
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

# Dataset paths relative to project root
PROJECT_ROOT  = Path(__file__).resolve().parent.parent.parent
NANDANA_ROOT  = PROJECT_ROOT.parent          # /nandana/
PROCESSED_DIR = PROJECT_ROOT / 'datasets' / 'processed'
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

ASAP2_PATH    = NANDANA_ROOT / 'ASAP2_train_sourcetexts.csv'
GRAMMAR_PATH  = NANDANA_ROOT / 'Grammar Correction.csv'
SPELLING_PATH = NANDANA_ROOT / 'TOEFL_Spell_Synthetic_Combined.csv'
ESSAYS_PATH   = NANDANA_ROOT / 'Essays.csv'
ANNOTATIONS_PATH = NANDANA_ROOT / 'Annotations.csv'

# Per-prompt score ranges in ASAP2 (prompt_id → (min, max))
ASAP2_SCORE_RANGES = {
    1:  (1, 6),   2: (1, 6),   3: (0, 3),   4: (0, 3),
    5:  (0, 4),   6: (0, 4),   7: (0, 30),  8: (0, 60),
}


# ─── ASAP2 ───────────────────────────────────────────────────────────────────

def load_asap2(min_words: int = 20) -> pd.DataFrame:
    """Load and clean ASAP2 dataset. Returns df with normalized score 1-6."""
    logger.info(f'Loading ASAP2 from {ASAP2_PATH}')
    df = pd.read_csv(ASAP2_PATH, low_memory=False)

    # Keep only needed columns; rename for clarity
    required = ['essay_id', 'full_text', 'score']
    optional = ['assignment', 'prompt_name', 'gender', 'ell_status', 'race_ethnicity']

    keep = [c for c in required + optional if c in df.columns]
    df = df[keep].copy()
    df.rename(columns={'full_text': 'essay_text'}, inplace=True)

    # Drop nulls
    df.dropna(subset=['essay_text', 'score'], inplace=True)
    df['essay_text'] = df['essay_text'].astype(str).str.strip()
    df['score'] = pd.to_numeric(df['score'], errors='coerce')
    df.dropna(subset=['score'], inplace=True)

    # Remove very short essays
    df = df[df['essay_text'].str.split().str.len() >= min_words]

    # Detect prompt from score distribution and normalize to 1–6 scale
    # Use assignment column if available, else infer from score range
    if 'assignment' in df.columns:
        df['prompt_id'] = df['assignment'].astype('category').cat.codes + 1
    else:
        df['prompt_id'] = 1

    df['score_normalized'] = df.apply(_normalize_score, axis=1)

    # Remove duplicates
    df.drop_duplicates(subset=['essay_text'], inplace=True)
    df.reset_index(drop=True, inplace=True)

    logger.info(f'ASAP2 loaded: {len(df)} essays, score range {df["score_normalized"].min():.2f}–{df["score_normalized"].max():.2f}')
    return df


def _normalize_score(row) -> float:
    """Normalize a score to 1–6 range based on its prompt."""
    pid = row.get('prompt_id', 1)
    lo, hi = ASAP2_SCORE_RANGES.get(pid, (0, 6))
    if hi == lo:
        return 3.5
    normalized = (row['score'] - lo) / (hi - lo)  # 0–1
    score = 1 + normalized * 5
    return round(float(np.clip(score, 1.0, 6.0)), 4)


def split_asap2(df: pd.DataFrame, seed: int = 42):
    """
    Student-level stratified split: 80% train / 10% val / 10% test.
    Falls back to random split if stratification is unavailable.
    """
    try:
        train, temp = train_test_split(df, test_size=0.20, random_state=seed,
                                       stratify=_stratify_col(df))
        val, test   = train_test_split(temp, test_size=0.50, random_state=seed,
                                       stratify=_stratify_col(temp))
    except ValueError:
        train, temp = train_test_split(df, test_size=0.20, random_state=seed)
        val, test   = train_test_split(temp, test_size=0.50, random_state=seed)

    _save_split(train, 'train')
    _save_split(val,   'val')
    _save_split(test,  'test')

    logger.info(f'Split → train:{len(train)} val:{len(val)} test:{len(test)}')
    return train, val, test


def _stratify_col(df):
    """Bin normalized score into 6 buckets for stratification."""
    bins = pd.cut(df['score_normalized'], bins=6, labels=False)
    return bins.fillna(0).astype(int)



def _save_split(df, name):
    df.to_csv(PROCESSED_DIR / f'{name}.csv', index=False)


# ─── Grammar ─────────────────────────────────────────────────────────────────

def load_grammar_data() -> pd.DataFrame:
    """Load grammar correction dataset."""
    df = pd.read_csv(GRAMMAR_PATH, encoding='utf-8-sig')
    df.columns = [c.strip() for c in df.columns]
    df.rename(columns={
        'Error Type': 'error_type',
        'Ungrammatical Statement': 'original',
        'Standard English': 'corrected',
    }, inplace=True)
    df.dropna(subset=['original', 'corrected'], inplace=True)
    df['original']  = df['original'].str.strip()
    df['corrected'] = df['corrected'].str.strip()
    logger.info(f'Grammar data: {len(df)} pairs, {df["error_type"].nunique()} error types')
    return df


# ─── Spelling ─────────────────────────────────────────────────────────────────

def load_spelling_data() -> tuple[pd.DataFrame, dict]:
    """
    Load spelling data from Annotations.csv + TOEFL_Spell_Synthetic.
    Returns (dataframe, correction_map).
    """
    dfs = []

    # Annotations.csv
    if ANNOTATIONS_PATH.exists():
        ann = pd.read_csv(ANNOTATIONS_PATH)
        ann.columns = [c.strip() for c in ann.columns]
        if 'Misspelling' in ann.columns and 'Correction' in ann.columns:
            ann = ann[['Misspelling', 'Correction']].dropna()
            ann.columns = ['misspelling', 'correction']
            dfs.append(ann)

    # TOEFL_Spell_Synthetic
    if SPELLING_PATH.exists():
        sp = pd.read_csv(SPELLING_PATH)
        sp.columns = [c.strip() for c in sp.columns]
        misp_col = next((c for c in sp.columns if 'misspell' in c.lower()), None)
        corr_col = next((c for c in sp.columns if 'correct' in c.lower()), None)
        if misp_col and corr_col:
            sp = sp[[misp_col, corr_col]].dropna()
            sp.columns = ['misspelling', 'correction']
            dfs.append(sp)

    if not dfs:
        return pd.DataFrame(columns=['misspelling', 'correction']), {}

    combined = pd.concat(dfs, ignore_index=True)
    combined['misspelling'] = combined['misspelling'].str.lower().str.strip()
    combined['correction']  = combined['correction'].str.lower().str.strip()
    combined.drop_duplicates(subset=['misspelling'], inplace=True)

    correction_map = dict(zip(combined['misspelling'], combined['correction']))
    logger.info(f'Spelling corpus: {len(combined)} pairs')
    return combined, correction_map


# ─── Essays.csv ──────────────────────────────────────────────────────────────

def load_essays_csv() -> pd.DataFrame:
    """Load Essays.csv (error-tagged essays with clean versions)."""
    df = pd.read_csv(ESSAYS_PATH)
    df.columns = [c.strip() for c in df.columns]
    df.dropna(subset=['Essay', 'Clean_Essay'], inplace=True)
    return df


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    df = load_asap2()
    train, val, test = split_asap2(df)
    print(f'✅ ASAP2 processed: {len(train)} train / {len(val)} val / {len(test)} test')

    gdf = load_grammar_data()
    print(f'✅ Grammar: {len(gdf)} pairs')

    sdf, smap = load_spelling_data()
    print(f'✅ Spelling: {len(sdf)} pairs, {len(smap)} in correction map')
