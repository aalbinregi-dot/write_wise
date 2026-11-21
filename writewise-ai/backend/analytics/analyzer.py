"""
Full Essay Analysis Orchestrator
Runs all modules in sequence and returns unified result dict.
"""
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def analyze_essay(text: str, student_history: list = None) -> dict:
    """
    Run the complete WriteWise AI analysis pipeline on essay text.

    Args:
        text:            Raw essay text
        student_history: List of previous EssayResult dicts for growth context

    Returns:
        Unified result dict ready to be stored as EssayResult.
    """
    if not text or not text.strip():
        return _error_result('Essay text is empty.')

    # ── 1. Linguistic features ─────────────────────────────────────────────
    from ml.features.linguistic_features import extract_features
    features = extract_features(text)

    # ── 2. Essay score ─────────────────────────────────────────────────────
    from ml.inference.scorer import score_essay
    scoring  = score_essay(text)
    score    = scoring['score']
    conf     = scoring['confidence']

    # ── 3. Grammar analysis ────────────────────────────────────────────────
    from backend.grammar.analyzer import analyze_grammar
    grammar  = analyze_grammar(text)

    # ── 4. Spelling analysis ───────────────────────────────────────────────
    from backend.spelling.analyzer import analyze_spelling
    spelling = analyze_spelling(text)

    # ── 5. Writing analysis (readability, vocab, structure, coherence) ─────
    writing  = _writing_analysis(text, features)

    # ── 6. Problem diagnosis ────────────────────────────────────────────────
    problems = _diagnose_problems(grammar, spelling, writing, score)

    # ── 7. Sentence corrections ─────────────────────────────────────────────
    corrections = _build_corrections(grammar['errors'][:5], spelling['errors'][:5])

    # ── 8. Writing advice ──────────────────────────────────────────────────
    advice = _generate_advice(problems, features)

    # ── 9. Personalized feedback (uses history) ─────────────────────────────
    personalized = _personalized_feedback(problems, student_history or [])

    # ── 10. Previous score for comparison ─────────────────────────────────
    prev_score = student_history[-1].get('predicted_score') if student_history else None

    return {
        # Scores
        'predicted_score':    score,
        'score_confidence':   conf,
        'previous_score':     prev_score,
        'final_score':        score,

        # Counts
        'word_count':         features['word_count'],
        'sentence_count':     features['sentence_count'],
        'paragraph_count':    features['paragraph_count'],
        'grammar_error_count':  grammar['error_count'],
        'spelling_error_count': spelling['error_count'],

        # Metrics
        'vocab_diversity':    features['type_token_ratio'],
        'readability_score':  features['flesch_reading_ease'],
        'readability_grade':  writing['readability_label'],
        'coherence_score':    writing['coherence_score'],
        'argument_score':     writing['argument_score'],

        # Detail blobs
        'grammar_errors':     grammar['errors'],
        'spelling_errors':    spelling['errors'],
        'linguistic_features': features,
        'writing_analysis':   writing,
        'problems':           problems,
        'corrections':        corrections,
        'feedback': {
            'advice':        advice,
            'personalized':  personalized,
            'model_version': scoring['model_version'],
        },
    }


def _writing_analysis(text: str, features: dict) -> dict:
    """Compute readability, vocabulary, structure, and coherence signals."""
    import textstat
    import nltk
    from nltk.tokenize import sent_tokenize

    # Readability
    fre = features['flesch_reading_ease']
    fkg = features['flesch_kincaid_grade']

    if fre >= 70:
        read_label = 'Easy'
    elif fre >= 50:
        read_label = 'Standard'
    elif fre >= 30:
        read_label = 'Difficult'
    else:
        read_label = 'Very Difficult'

    # Vocabulary quality
    ttr    = features['type_token_ratio']
    acad   = features['academic_word_ratio']
    repeat = features['repetition_ratio']

    if ttr >= 0.55 and acad >= 0.04:
        vocab_quality = 'Excellent'
    elif ttr >= 0.40:
        vocab_quality = 'Good'
    elif ttr >= 0.25:
        vocab_quality = 'Fair'
    else:
        vocab_quality = 'Needs Improvement'

    # Structure analysis
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    has_intro  = features.get('has_introduction', 0)
    has_conc   = features.get('has_conclusion', 0)
    transitions = features.get('transition_count', 0)

    if len(paragraphs) >= 3 and has_intro and has_conc and transitions >= 3:
        structure_quality = 'Good'
    elif len(paragraphs) >= 2 and transitions >= 1:
        structure_quality = 'Fair'
    else:
        structure_quality = 'Needs Improvement'

    # Coherence (heuristic: sentence overlap + transition density)
    sentences = sent_tokenize(text)
    coherence_score = _coherence_heuristic(sentences, transitions, len(paragraphs))

    # Argument development (heuristic: avg paragraph length, evidence words)
    evidence_words = {'because', 'since', 'for example', 'for instance',
                      'evidence', 'research', 'shows', 'suggests', 'demonstrates',
                      'studies', 'according', 'therefore', 'thus', 'proves'}
    evidence_count = sum(1 for w in evidence_words if w in text.lower())
    argument_score = min(evidence_count / 5, 1.0) * 5 + (1 if len(paragraphs) >= 3 else 0)
    argument_score = round(min(argument_score, 6), 2)

    if argument_score >= 4.5:
        arg_quality = 'Strong'
    elif argument_score >= 3.0:
        arg_quality = 'Moderate'
    else:
        arg_quality = 'Needs Work'

    # Overused words
    import re
    from collections import Counter
    words_lower = re.findall(r'\b[a-z]+\b', text.lower())
    from nltk.corpus import stopwords
    try:
        stop = set(stopwords.words('english'))
    except Exception:
        stop = set()
    content = [w for w in words_lower if w not in stop and len(w) > 3]
    freq    = Counter(content)
    overused = [{'word': w, 'count': c} for w, c in freq.most_common(5) if c >= 3]

    return {
        'readability_label':  read_label,
        'readability_score':  fre,
        'grade_level':        fkg,
        'vocab_quality':      vocab_quality,
        'vocab_diversity':    round(ttr, 4),
        'academic_ratio':     round(acad, 4),
        'repetition_ratio':   round(repeat, 4),
        'overused_words':     overused,
        'structure_quality':  structure_quality,
        'has_introduction':   bool(has_intro),
        'has_conclusion':     bool(has_conc),
        'transition_count':   transitions,
        'paragraph_count':    len(paragraphs),
        'coherence_score':    coherence_score,
        'argument_score':     argument_score,
        'argument_quality':   arg_quality,
    }


def _coherence_heuristic(sentences: list, transition_count: int, para_count: int) -> float:
    """Simple coherence score 0–5 based on transitions and paragraph structure."""
    base = min(transition_count / 3, 1.5)
    struct = 1.0 if para_count >= 3 else 0.5
    length_penalty = 0.5 if len(sentences) < 3 else 0.0
    score = min((base + struct - length_penalty) * (5 / 2.5), 5.0)
    return round(max(score, 0), 2)


def _diagnose_problems(grammar, spelling, writing, score) -> list:
    """Classify detected problems into HIGH/MEDIUM/LOW priority."""
    problems = []

    if grammar['error_count'] >= 8:
        problems.append({'priority': 'HIGH',   'category': 'Grammar',
                         'title': 'Multiple Grammar Errors',
                         'description': f'{grammar["error_count"]} grammar errors detected. '
                                        'Focus on subject-verb agreement and verb tenses.',
                         'error_types': list(grammar['error_types'].keys())[:3]})
    elif grammar['error_count'] >= 3:
        problems.append({'priority': 'MEDIUM', 'category': 'Grammar',
                         'title': 'Some Grammar Errors',
                         'description': f'{grammar["error_count"]} grammar errors found.',
                         'error_types': list(grammar['error_types'].keys())[:2]})

    if spelling['error_count'] >= 5:
        problems.append({'priority': 'HIGH',   'category': 'Spelling',
                         'title': 'Frequent Spelling Errors',
                         'description': f'{spelling["error_count"]} spelling errors detected.'})
    elif spelling['error_count'] >= 2:
        problems.append({'priority': 'MEDIUM', 'category': 'Spelling',
                         'title': 'Spelling Errors',
                         'description': f'{spelling["error_count"]} spelling mistakes found.'})

    if writing['argument_quality'] == 'Needs Work':
        problems.append({'priority': 'HIGH',   'category': 'Argument Development',
                         'title': 'Weak Argument Support',
                         'description': 'Claims are not well supported with evidence or examples. '
                                        'Add specific reasons, examples, or data.'})
    elif writing['argument_quality'] == 'Moderate':
        problems.append({'priority': 'MEDIUM', 'category': 'Argument Development',
                         'title': 'Argument Needs Strengthening',
                         'description': 'Some claims lack supporting evidence.'})

    if not writing['has_introduction'] or not writing['has_conclusion']:
        problems.append({'priority': 'HIGH',   'category': 'Structure',
                         'title': 'Missing Introduction or Conclusion',
                         'description': 'A clear introduction and conclusion are essential for essay structure.'})
    elif writing['transition_count'] < 2:
        problems.append({'priority': 'MEDIUM', 'category': 'Structure',
                         'title': 'Weak Paragraph Transitions',
                         'description': 'Use transition words to connect ideas between paragraphs.'})

    if writing['vocab_quality'] in ['Fair', 'Needs Improvement']:
        problems.append({'priority': 'MEDIUM', 'category': 'Vocabulary',
                         'title': 'Limited Vocabulary Range',
                         'description': 'Expand vocabulary diversity. '
                                        f'Type-token ratio: {writing["vocab_diversity"]:.2f}.'})

    if writing['overused_words']:
        overused_str = ', '.join(f'"{w["word"]}" ×{w["count"]}' for w in writing['overused_words'][:3])
        problems.append({'priority': 'LOW',    'category': 'Vocabulary',
                         'title': 'Repeated Words',
                         'description': f'Words used frequently: {overused_str}.'})

    if writing['readability_label'] == 'Very Difficult':
        problems.append({'priority': 'MEDIUM', 'category': 'Readability',
                         'title': 'Overly Complex Sentences',
                         'description': 'Some sentences may be too long or complex. Aim for clarity.'})

    return sorted(problems, key=lambda x: {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}[x['priority']])


def _build_corrections(grammar_errors: list, spelling_errors: list) -> list:
    corrections = []
    for e in grammar_errors:
        if e.get('correction'):
            corrections.append({
                'type':        'grammar',
                'original':    e['original'],
                'correction':  e['correction'],
                'explanation': e.get('explanation', ''),
                'error_type':  e.get('error_type', ''),
            })
    for e in spelling_errors:
        corrections.append({
            'type':        'spelling',
            'original':    e['misspelling'],
            'correction':  e['correction'],
            'explanation': f'"{e["misspelling"]}" should be "{e["correction"]}".',
            'error_type':  'Spelling Error',
        })
    return corrections


def _generate_advice(problems: list, features: dict) -> list:
    advice = []
    categories = {p['category'] for p in problems}

    if 'Grammar' in categories:
        advice.append({
            'area': 'Grammar',
            'advice': 'Review subject-verb agreement, verb tenses, and article usage. '
                      'Read each sentence aloud to catch errors naturally.',
        })
    if 'Argument Development' in categories:
        advice.append({
            'area': 'Argument Development',
            'advice': 'Structure each body paragraph as: Topic Sentence → Explanation → '
                      'Evidence/Example → Analysis → Transition.',
        })
    if 'Structure' in categories:
        advice.append({
            'area': 'Essay Structure',
            'advice': 'Introduction: introduce topic + state your position. '
                      'Body: one idea per paragraph with evidence. '
                      'Conclusion: restate position + key points (no new arguments).',
        })
    if 'Vocabulary' in categories:
        advice.append({
            'area': 'Vocabulary',
            'advice': 'Replace frequently repeated words with precise alternatives. '
                      'Read academic texts to expand your active vocabulary.',
        })
    if 'Spelling' in categories:
        advice.append({
            'area': 'Spelling',
            'advice': 'Proofread carefully before submitting. '
                      'Use spell-check as a first pass but do not rely on it alone.',
        })

    if not advice:
        advice.append({
            'area': 'General',
            'advice': 'Your essay is well-written. Focus on deepening your arguments '
                      'and expanding vocabulary to reach a higher score.',
        })

    return advice


def _personalized_feedback(problems: list, history: list) -> str:
    if not history:
        return ('This is your first submission. Focus on the High-Priority problems listed above. '
                'Submit another essay after completing the recommended lessons to track your growth.')

    prev_grammar  = sum(h.get('grammar_error_count', 0)  for h in history[-3:]) / max(len(history[-3:]), 1)
    prev_spelling = sum(h.get('spelling_error_count', 0) for h in history[-3:]) / max(len(history[-3:]), 1)
    prev_score    = history[-1].get('predicted_score', 0)

    lines = []
    current_categories = {p['category'] for p in problems}

    if 'Grammar' not in current_categories and prev_grammar > 3:
        lines.append('✓ Your grammar has improved significantly compared to earlier submissions.')
    if 'Spelling' not in current_categories and prev_spelling > 2:
        lines.append('✓ Spelling errors have decreased — great progress.')

    top_problem = problems[0] if problems else None
    if top_problem:
        lines.append(f'Your current main focus area is {top_problem["category"]}. '
                     f'{top_problem["description"]}')

    lines.append('Keep submitting essays to track your writing growth over time.')
    return ' '.join(lines)


def _error_result(message: str) -> dict:
    return {
        'error':         True,
        'error_message': message,
        'predicted_score': None,
        'grammar_error_count': 0,
        'spelling_error_count': 0,
        'problems': [],
    }
