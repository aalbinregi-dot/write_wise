"""
ML Linguistic Feature Extractor
Extracts basic, vocabulary, readability, and structure features from essay text.
"""
import re
import math
import string
from collections import Counter

import nltk
import textstat

# Download NLTK data if needed
for resource in ['punkt', 'averaged_perceptron_tagger', 'stopwords']:
    try:
        nltk.download(resource, quiet=True)
    except Exception:
        pass


from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk import pos_tag

STOP_WORDS = set(stopwords.words('english'))

ACADEMIC_WORDS = {
    'analyze', 'analysis', 'argue', 'argument', 'concept', 'conclude',
    'conclusion', 'consequently', 'constitute', 'context', 'contribute',
    'create', 'demonstrate', 'develop', 'distinct', 'establish', 'evaluate',
    'evidence', 'examine', 'factor', 'furthermore', 'however', 'identify',
    'indicate', 'individual', 'interpret', 'maintain', 'method', 'occur',
    'therefore', 'significant', 'specific', 'theory', 'thus', 'approach',
    'assume', 'assumption', 'benefit', 'category', 'consequently', 'data',
    'define', 'definition', 'derive', 'distribution', 'environment',
    'furthermore', 'generate', 'impact', 'implication', 'include', 'indicate',
    'involve', 'issue', 'justify', 'major', 'obtain', 'occur', 'outcome',
    'perspective', 'policy', 'principle', 'process', 'require', 'research',
    'respond', 'role', 'structure', 'suggest', 'summarize',
}

TRANSITION_WORDS = {
    'however', 'therefore', 'furthermore', 'moreover', 'consequently',
    'additionally', 'nevertheless', 'nonetheless', 'thus', 'hence',
    'meanwhile', 'subsequently', 'conversely', 'alternatively', 'similarly',
    'specifically', 'particularly', 'for example', 'for instance',
    'in conclusion', 'in summary', 'in addition', 'as a result',
    'on the other hand', 'in contrast', 'first', 'second', 'finally',
    'in other words', 'that is', 'namely',
}


def extract_features(text: str) -> dict:
    """
    Extract a comprehensive set of linguistic features from essay text.
    Returns a dict of named float/int features.
    """
    if not text or not text.strip():
        return _empty_features()

    # Basic tokenisation
    sentences  = sent_tokenize(text)
    words_raw  = word_tokenize(text)
    words      = [w for w in words_raw if w.isalpha()]
    words_lower = [w.lower() for w in words]
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    word_count      = len(words)
    char_count      = len(text.replace(' ', ''))
    sentence_count  = max(len(sentences), 1)
    paragraph_count = max(len(paragraphs), 1)

    avg_sentence_len = word_count / sentence_count
    avg_word_len     = sum(len(w) for w in words) / max(word_count, 1)

    # Vocabulary
    unique_words    = set(words_lower)
    ttr             = len(unique_words) / max(word_count, 1)
    content_words   = [w for w in words_lower if w not in STOP_WORDS]
    content_unique  = set(content_words)

    word_freq = Counter(words_lower)
    most_common_words = word_freq.most_common(5)
    repetition_ratio  = sum(c for _, c in most_common_words if c > 3) / max(word_count, 1)

    academic_count    = sum(1 for w in words_lower if w in ACADEMIC_WORDS)
    academic_ratio    = academic_count / max(word_count, 1)

    # Transition words
    text_lower = text.lower()
    transition_count = sum(1 for t in TRANSITION_WORDS if t in text_lower)

    # POS distribution
    tagged = pos_tag(words[:200])   # limit for performance
    pos_counts = Counter(tag[:2] for _, tag in tagged)
    total_pos = max(sum(pos_counts.values()), 1)
    noun_ratio  = pos_counts.get('NN', 0) / total_pos
    verb_ratio  = pos_counts.get('VB', 0) / total_pos
    adj_ratio   = pos_counts.get('JJ', 0) / total_pos
    adv_ratio   = pos_counts.get('RB', 0) / total_pos

    # Readability
    flesch_reading_ease = _safe(lambda: textstat.flesch_reading_ease(text))
    flesch_kincaid_grade = _safe(lambda: textstat.flesch_kincaid_grade(text))
    gunning_fog         = _safe(lambda: textstat.gunning_fog(text))
    smog_index          = _safe(lambda: textstat.smog_index(text))
    automated_readability = _safe(lambda: textstat.automated_readability_index(text))

    # Structure signals
    has_intro      = int(len(paragraphs) >= 3)
    has_conclusion = int(len(paragraphs) >= 3 and any(
        k in paragraphs[-1].lower() for k in ['conclusion', 'summary', 'therefore', 'thus', 'finally', 'overall']
    ))
    sentence_len_variance = _variance([len(word_tokenize(s)) for s in sentences])

    # Sentence complexity
    complex_sentences = sum(1 for s in sentences if len(word_tokenize(s)) > 20)
    complex_ratio     = complex_sentences / sentence_count

    return {
        # Basic
        'word_count':            word_count,
        'char_count':            char_count,
        'sentence_count':        sentence_count,
        'paragraph_count':       paragraph_count,
        'avg_sentence_length':   round(avg_sentence_len, 2),
        'avg_word_length':       round(avg_word_len, 2),

        # Vocabulary
        'unique_word_count':     len(unique_words),
        'type_token_ratio':      round(ttr, 4),
        'content_word_count':    len(content_words),
        'content_word_diversity': round(len(content_unique) / max(len(content_words), 1), 4),
        'academic_word_count':   academic_count,
        'academic_word_ratio':   round(academic_ratio, 4),
        'repetition_ratio':      round(repetition_ratio, 4),
        'top_words':             [w for w, _ in most_common_words],

        # POS
        'noun_ratio': round(noun_ratio, 4),
        'verb_ratio': round(verb_ratio, 4),
        'adj_ratio':  round(adj_ratio, 4),
        'adv_ratio':  round(adv_ratio, 4),

        # Structure
        'transition_count':         transition_count,
        'has_introduction':         has_intro,
        'has_conclusion':           has_conclusion,
        'complex_sentence_ratio':   round(complex_ratio, 4),
        'sentence_len_variance':    round(sentence_len_variance, 4),

        # Readability
        'flesch_reading_ease':      round(flesch_reading_ease, 2),
        'flesch_kincaid_grade':     round(flesch_kincaid_grade, 2),
        'gunning_fog':              round(gunning_fog, 2),
        'smog_index':               round(smog_index, 2),
        'automated_readability':    round(automated_readability, 2),
    }


def get_feature_vector(features: dict) -> list:
    """Return a flat numeric list for ML model input."""
    keys = [
        'word_count', 'sentence_count', 'paragraph_count',
        'avg_sentence_length', 'avg_word_length',
        'type_token_ratio', 'academic_word_ratio', 'repetition_ratio',
        'noun_ratio', 'verb_ratio', 'adj_ratio', 'adv_ratio',
        'transition_count', 'has_introduction', 'has_conclusion',
        'complex_sentence_ratio', 'sentence_len_variance',
        'flesch_reading_ease', 'flesch_kincaid_grade', 'gunning_fog',
    ]
    return [float(features.get(k, 0.0)) for k in keys]


def _safe(fn, default=0.0):
    try:
        return fn()
    except Exception:
        return default


def _variance(values: list) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return sum((x - mean) ** 2 for x in values) / len(values)


def _empty_features() -> dict:
    return {k: 0 for k in [
        'word_count', 'char_count', 'sentence_count', 'paragraph_count',
        'avg_sentence_length', 'avg_word_length', 'unique_word_count',
        'type_token_ratio', 'content_word_count', 'content_word_diversity',
        'academic_word_count', 'academic_word_ratio', 'repetition_ratio',
        'noun_ratio', 'verb_ratio', 'adj_ratio', 'adv_ratio',
        'transition_count', 'has_introduction', 'has_conclusion',
        'complex_sentence_ratio', 'sentence_len_variance',
        'flesch_reading_ease', 'flesch_kincaid_grade', 'gunning_fog',
        'smog_index', 'automated_readability',
    ]}
