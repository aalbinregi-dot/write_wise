"""
Grammar Analysis Module
Detects grammar errors using LanguageTool + augments with Grammar Correction dataset.
"""
import re
import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

# Load grammar correction dataset pairs at module startup
_GRAMMAR_DB = {}
_ERROR_TYPES = []

def _load_grammar_db():
    global _GRAMMAR_DB, _ERROR_TYPES
    if _GRAMMAR_DB:
        return
    try:
        path = Path(__file__).resolve().parent.parent.parent.parent / 'Grammar Correction.csv'
        if path.exists():
            df = pd.read_csv(path, encoding='utf-8-sig')
            df.columns = [c.strip() for c in df.columns]
            df = df.rename(columns={
                'Error Type': 'error_type',
                'Ungrammatical Statement': 'original',
                'Standard English': 'corrected',
            }).dropna()
            for _, row in df.iterrows():
                _GRAMMAR_DB[row['original'].strip().lower()] = {
                    'corrected': row['corrected'].strip(),
                    'error_type': row['error_type'].strip(),
                }
            _ERROR_TYPES = df['error_type'].unique().tolist()
            logger.info(f'Grammar DB loaded: {len(_GRAMMAR_DB)} pairs')
    except Exception as e:
        logger.warning(f'Grammar DB load failed: {e}')


def analyze_grammar(text: str) -> dict:
    """
    Detect grammar errors in essay text.
    Returns list of errors with type, location, correction, explanation.
    """
    _load_grammar_db()
    errors = []

    # Try LanguageTool if available
    lt_errors = _languagetool_check(text)
    errors.extend(lt_errors)

    # Add rule-based checks for common patterns
    rule_errors = _rule_based_check(text)
    for e in rule_errors:
        # Avoid duplicates
        if not any(abs(e['offset'] - x['offset']) < 5 for x in errors):
            errors.append(e)

    # Sort by position
    errors.sort(key=lambda x: x.get('offset', 0))

    summary = _summarize_errors(errors)

    return {
        'errors':       errors,
        'error_count':  len(errors),
        'errors_per_100': round(len(errors) / max(_word_count(text), 1) * 100, 2),
        'error_types':  summary,
    }


def _languagetool_check(text: str) -> list:
    """Use LanguageTool Java server if available, else return empty."""
    try:
        import language_tool_python
        tool = language_tool_python.LanguageTool('en-US')
        matches = tool.check(text)
        errors = []
        for m in matches[:30]:  # cap for performance
            errors.append({
                'original':    text[m.offset:m.offset + m.errorLength],
                'correction':  m.replacements[0] if m.replacements else '',
                'error_type':  _map_lt_category(m.category),
                'explanation': m.message,
                'offset':      m.offset,
                'context':     m.context,
                'confidence':  0.85,
                'source':      'LanguageTool',
            })
        tool.close()
        return errors
    except Exception:
        return _rule_based_check(text)


RULE_PATTERNS = [
    # Subject-verb agreement
    (r'\b(they|students|people|children)\s+(is|was)\b',
     'Subject-Verb Agreement',
     'Plural subject requires plural verb (are/were).',
     lambda m: m.group().replace(m.group(2), 'are' if m.group(2) == 'is' else 'were')),
    (r'\b(he|she|it)\s+(are|were)\b',
     'Subject-Verb Agreement',
     'Singular subject requires singular verb (is/was).',
     lambda m: m.group().replace(m.group(2), 'is' if m.group(2) == 'are' else 'was')),
    # Article errors
    (r'\ba\s+[aeiouAEIOU]\w+',
     'Article Error',
     'Use "an" before words starting with a vowel sound.',
     lambda m: m.group().replace('a ', 'an ', 1)),
    # Double negatives
    (r"\b(don't|doesn't|didn't|can't|won't)\s+\w*\s*(no|nothing|nowhere|nobody|neither)\b",
     'Double Negative',
     'Avoid using two negatives in the same clause.',
     lambda m: m.group()),
    # Missing comma after introductory phrase
    (r'^(However|Furthermore|Moreover|Nevertheless|Therefore|Consequently|Additionally)\s+[^,]',
     'Punctuation Error',
     'Introductory adverbs should be followed by a comma.',
     lambda m: m.group()),
]


def _rule_based_check(text: str) -> list:
    errors = []
    for pattern, error_type, explanation, suggest_fn in RULE_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
            try:
                suggestion = suggest_fn(m)
            except Exception:
                suggestion = ''
            errors.append({
                'original':   m.group(),
                'correction': suggestion,
                'error_type': error_type,
                'explanation': explanation,
                'offset':     m.start(),
                'context':    text[max(0, m.start()-30):m.end()+30],
                'confidence': 0.70,
                'source':     'rule-based',
            })
    return errors


def _map_lt_category(cat: str) -> str:
    mapping = {
        'GRAMMAR':      'Grammar Error',
        'TYPOS':        'Spelling Error',
        'PUNCTUATION':  'Punctuation Error',
        'STYLE':        'Style Issue',
        'SEMANTICS':    'Word Choice',
    }
    return mapping.get(cat, cat)


def _summarize_errors(errors: list) -> dict:
    summary = {}
    for e in errors:
        t = e.get('error_type', 'Unknown')
        summary[t] = summary.get(t, 0) + 1
    return dict(sorted(summary.items(), key=lambda x: -x[1]))


def _word_count(text: str) -> int:
    return len(text.split())
