"""
Spelling Analysis Module
Detects spelling errors using pyspellchecker + correction map from Annotations.csv
"""
import re
import logging
from pathlib import Path
from functools import lru_cache

logger = logging.getLogger(__name__)

# Known technical terms and proper nouns that shouldn't be flagged
WHITELIST = {
    'ai', 'ml', 'nlp', 'api', 'ielts', 'toefl', 'toeic', 'cefr',
    'covid', 'internet', 'online', 'smartphone', 'blockchain', 'cryptocurrency',
}


@lru_cache(maxsize=1)
def _get_spell_checker():
    from spellchecker import SpellChecker
    return SpellChecker()


@lru_cache(maxsize=1)
def _get_correction_map() -> dict:
    """Load the correction map from Annotations + TOEFL_Spell datasets."""
    correction_map = {}
    nandana_root = Path(__file__).resolve().parent.parent.parent.parent

    # Annotations.csv
    ann_path = nandana_root / 'Annotations.csv'
    if ann_path.exists():
        import pandas as pd
        try:
            df = pd.read_csv(ann_path)
            df.columns = [c.strip() for c in df.columns]
            if 'Misspelling' in df.columns and 'Correction' in df.columns:
                for _, row in df.dropna(subset=['Misspelling', 'Correction']).iterrows():
                    correction_map[str(row['Misspelling']).lower().strip()] = str(row['Correction']).lower().strip()
        except Exception as e:
            logger.warning(f'Could not load Annotations.csv: {e}')

    # TOEFL_Spell_Synthetic
    toefl_path = nandana_root / 'TOEFL_Spell_Synthetic_Combined.csv'
    if toefl_path.exists():
        import pandas as pd
        try:
            df = pd.read_csv(toefl_path)
            df.columns = [c.strip() for c in df.columns]
            misp = next((c for c in df.columns if 'misspell' in c.lower()), None)
            corr = next((c for c in df.columns if 'correct' in c.lower()), None)
            if misp and corr:
                for _, row in df.dropna(subset=[misp, corr]).iterrows():
                    correction_map[str(row[misp]).lower().strip()] = str(row[corr]).lower().strip()
        except Exception as e:
            logger.warning(f'Could not load TOEFL Spell data: {e}')

    logger.info(f'Spelling correction map: {len(correction_map)} entries')
    return correction_map


def analyze_spelling(text: str) -> dict:
    """
    Detect spelling errors in essay text.
    Returns: { errors, error_count, error_rate }
    """
    correction_map = _get_correction_map()

    # Tokenise keeping position
    tokens = list(_tokenize_with_positions(text))
    words  = [(pos, word) for pos, word in tokens
              if word.isalpha() and len(word) > 1 and word.lower() not in WHITELIST]

    errors = []
    seen   = set()

    try:
        spell    = _get_spell_checker()
        word_list = [w for _, w in words]
        misspelled = spell.unknown(word_list)

        for pos, word in words:
            lower = word.lower()
            if lower in misspelled and lower not in seen:
                seen.add(lower)
                # Look up correction: prefer dataset map, then spellchecker
                correction = (correction_map.get(lower)
                              or spell.correction(lower)
                              or word)
                errors.append({
                    'misspelling':  word,
                    'correction':   correction,
                    'offset':       pos,
                    'confidence':   0.85 if lower in correction_map else 0.70,
                    'context':      text[max(0, pos - 25):pos + len(word) + 25],
                    'source':       'dataset' if lower in correction_map else 'spellchecker',
                })
    except Exception as e:
        # Pure dataset-map fallback
        for pos, word in words:
            lower = word.lower()
            if lower in correction_map and lower not in seen:
                seen.add(lower)
                errors.append({
                    'misspelling': word,
                    'correction':  correction_map[lower],
                    'offset':      pos,
                    'confidence':  0.90,
                    'context':     text[max(0, pos - 25):pos + len(word) + 25],
                    'source':      'dataset',
                })

    word_count = max(len(words), 1)
    return {
        'errors':          errors,
        'error_count':     len(errors),
        'error_rate':      round(len(errors) / word_count * 100, 2),
        'words_checked':   len(words),
    }


def _tokenize_with_positions(text: str):
    """Yield (start_offset, word) for each word token."""
    for m in re.finditer(r'\b[a-zA-Z]+\b', text):
        yield m.start(), m.group()
