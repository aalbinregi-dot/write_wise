"""
Plagiarism Detection Engine
Compares submitted text against a reference corpus using:
  - N-gram fingerprinting (Winnowing algorithm)
  - TF-IDF cosine similarity
  - Sentence-level overlap detection
"""
import re
import math
from collections import Counter


# ── Reference corpus ──────────────────────────────────────────────────────────
# A built-in collection of commonly submitted / web-sourced texts used for
# similarity comparison. Extend this list to improve detection coverage.
REFERENCE_CORPUS = [
    {
        "source": "Common Academic Essay — Technology in Education",
        "text": (
            "Technology has significantly changed the way students learn and teachers teach in modern education. "
            "The integration of digital tools in classrooms has opened up new possibilities for personalized learning. "
            "Students can now access vast resources online, collaborate with peers across the world, and receive "
            "immediate feedback on their work. However, there are also challenges associated with this transformation. "
            "Many students are distracted by social media and entertainment platforms. Furthermore technology access "
            "remains unequal across different socioeconomic groups. Despite these challenges, the benefits of "
            "technology in education outweigh the drawbacks when implemented thoughtfully."
        ),
    },
    {
        "source": "Common Academic Essay — Environmental Protection",
        "text": (
            "Protecting the environment is one of the most urgent priorities of our time. Industrial activities "
            "and excessive consumption have led to severe pollution, climate change, and habitat loss. "
            "Governments must enforce stricter regulations on carbon emissions and promote renewable energy "
            "sources like solar and wind power. Additionally individuals should adopt sustainable habits such "
            "as reducing waste, recycling, and conserving energy. Without a healthy planet, long-term prosperity "
            "is impossible. Environmental conservation requires collective effort from governments, corporations, "
            "and individuals to secure a sustainable future for upcoming generations."
        ),
    },
    {
        "source": "Common Essay — Social Media and Mental Health",
        "text": (
            "The impact of social media on modern society has been both profound and controversial. "
            "Many people today spend several hours each day scrolling through their feeds, often without "
            "realising the effect it has on their mental health. Research has shown that excessive use of "
            "platforms like Instagram and TikTok can lead to feelings of inadequacy, anxiety, and loneliness, "
            "particularly among younger users. However, social media also provides a powerful tool for "
            "communication, activism, and the rapid spread of information. It allows individuals to connect "
            "with others across the globe and gives voice to marginalised communities who were previously unheard."
        ),
    },
    {
        "source": "Wikipedia — Artificial Intelligence (excerpt)",
        "text": (
            "Artificial intelligence is intelligence demonstrated by machines, as opposed to the natural "
            "intelligence displayed by animals including humans. AI research has been defined as the field "
            "of study of intelligent agents, which refers to any system that perceives its environment and "
            "takes actions that maximize its chance of achieving its goals. The term artificial intelligence "
            "had previously been used to describe machines that mimic and display human cognitive skills "
            "associated with the human mind, such as learning and problem-solving."
        ),
    },
    {
        "source": "Common Essay — Climate Change",
        "text": (
            "Climate change represents one of the greatest challenges facing humanity today. The burning of "
            "fossil fuels, deforestation, and industrial processes have significantly increased the concentration "
            "of greenhouse gases in the atmosphere. This has led to a rise in global temperatures, resulting "
            "in melting ice caps, rising sea levels, and more frequent extreme weather events. Scientists "
            "warn that without immediate and drastic action to reduce carbon emissions, the consequences "
            "could be catastrophic for both human civilization and biodiversity."
        ),
    },
    {
        "source": "Common Essay — Globalisation",
        "text": (
            "Globalisation refers to the process by which businesses and other organisations develop "
            "international influence or begin operating on an international scale. It has led to increased "
            "trade, investment, and cultural exchange between nations. While globalisation has brought "
            "economic growth and improved living standards in many parts of the world, it has also been "
            "criticised for widening inequality, exploiting developing nations, and eroding local cultures. "
            "The debate over the benefits and drawbacks of globalisation continues to shape international "
            "politics and economic policy."
        ),
    },
]


# ── Text utilities ─────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def _tokenize(text: str) -> list[str]:
    return _clean(text).split()


def _ngrams(tokens: list[str], n: int) -> set[str]:
    return {' '.join(tokens[i:i+n]) for i in range(len(tokens) - n + 1)}


def _tfidf_vector(text: str, corpus_texts: list[str]) -> dict[str, float]:
    """Build a simple TF-IDF vector for the given text."""
    tokens = _tokenize(text)
    tf = Counter(tokens)
    total = len(tokens) or 1
    tf = {k: v / total for k, v in tf.items()}

    all_texts = [text] + corpus_texts
    idf = {}
    for term in tf:
        df = sum(1 for t in all_texts if term in _tokenize(t))
        idf[term] = math.log((len(all_texts) + 1) / (df + 1)) + 1

    return {term: tf[term] * idf[term] for term in tf}


def _cosine_similarity(vec_a: dict, vec_b: dict) -> float:
    common = set(vec_a) & set(vec_b)
    if not common:
        return 0.0
    dot = sum(vec_a[k] * vec_b.get(k, 0) for k in common)
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _sentence_overlap(text: str, reference: str) -> list[dict]:
    """Find sentences in text that closely match sentences in reference."""
    def split_sentences(t):
        return [s.strip() for s in re.split(r'[.!?]+', t) if len(s.strip()) > 20]

    text_sentences = split_sentences(text)
    ref_sentences = split_sentences(reference)
    matches = []

    for ts in text_sentences:
        ts_ngrams = _ngrams(_tokenize(ts), 3)
        if not ts_ngrams:
            continue
        best_score = 0.0
        best_ref = ''
        for rs in ref_sentences:
            rs_ngrams = _ngrams(_tokenize(rs), 3)
            if not rs_ngrams:
                continue
            overlap = len(ts_ngrams & rs_ngrams) / len(ts_ngrams | rs_ngrams)
            if overlap > best_score:
                best_score = overlap
                best_ref = rs
        if best_score >= 0.35:
            matches.append({
                'submitted_sentence': ts,
                'matched_sentence': best_ref,
                'similarity': round(best_score * 100, 1),
            })

    return matches


# ── Main entry point ───────────────────────────────────────────────────────────

def check_plagiarism(text: str) -> dict:
    """
    Run plagiarism detection on `text`.

    Returns:
        {
          'score': float (0–100),
          'verdict': str,
          'verdict_color': str,
          'matches': [{ source, similarity, matched_sentences }],
          'total_sentences': int,
          'flagged_sentences': int,
        }
    """
    if not text or not text.strip():
        return {'score': 0, 'verdict': 'No text provided', 'verdict_color': 'green', 'matches': []}

    corpus_texts = [ref['text'] for ref in REFERENCE_CORPUS]
    vec_input = _tfidf_vector(text, corpus_texts)

    source_matches = []
    flagged_sentences_all = []

    for ref in REFERENCE_CORPUS:
        vec_ref = _tfidf_vector(ref['text'], corpus_texts)
        cosine_sim = _cosine_similarity(vec_input, vec_ref)

        # N-gram overlap (bigrams)
        input_tokens = _tokenize(text)
        ref_tokens = _tokenize(ref['text'])
        input_bigrams = _ngrams(input_tokens, 2)
        ref_bigrams = _ngrams(ref_tokens, 2)
        if input_bigrams | ref_bigrams:
            ngram_sim = len(input_bigrams & ref_bigrams) / len(input_bigrams | ref_bigrams)
        else:
            ngram_sim = 0.0

        # Combined similarity
        combined = (cosine_sim * 0.5) + (ngram_sim * 0.5)

        # Sentence-level matching
        sentence_matches = _sentence_overlap(text, ref['text'])
        flagged_sentences_all.extend(sentence_matches)

        if combined > 0.08 or sentence_matches:
            source_matches.append({
                'source': ref['source'],
                'similarity': round(combined * 100, 1),
                'cosine_similarity': round(cosine_sim * 100, 1),
                'ngram_similarity': round(ngram_sim * 100, 1),
                'matched_sentences': sentence_matches,
            })

    # Sort by similarity desc
    source_matches.sort(key=lambda x: x['similarity'], reverse=True)

    # Overall score = weighted combination
    if source_matches:
        top_sim = source_matches[0]['similarity']
        sentence_contribution = min(len(flagged_sentences_all) * 8, 40)
        overall = min(round((top_sim * 0.6) + sentence_contribution * 0.4), 100)
    else:
        overall = 0

    # Deduplicate flagged sentences
    seen = set()
    unique_flagged = []
    for s in flagged_sentences_all:
        key = s['submitted_sentence'][:60]
        if key not in seen:
            seen.add(key)
            unique_flagged.append(s)

    # Count sentences in submission
    submission_sentences = [s.strip() for s in re.split(r'[.!?]+', text) if len(s.strip()) > 20]

    # Verdict
    if overall >= 70:
        verdict = 'High Plagiarism Risk'
        verdict_color = '#F43F5E'
    elif overall >= 40:
        verdict = 'Moderate Similarity Detected'
        verdict_color = '#F59E0B'
    elif overall >= 15:
        verdict = 'Low Similarity'
        verdict_color = '#3B82F6'
    else:
        verdict = 'Likely Original'
        verdict_color = '#10B981'

    return {
        'score': overall,
        'verdict': verdict,
        'verdict_color': verdict_color,
        'matches': source_matches,
        'flagged_sentences': unique_flagged,
        'total_sentences': len(submission_sentences),
        'flagged_sentence_count': len(unique_flagged),
    }
