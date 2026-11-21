"""
AI Text Humanizer
Rewrites AI-generated text to sound more natural and human by:
  - Replacing overly formal / AI-typical phrases
  - Varying sentence structure and length
  - Adding natural connectors and hedging language
  - Introducing minor contractions
  - Breaking up overly long or monotone sentences
"""
import re
import random

# ── Phrase substitution map ───────────────────────────────────────────────────
# Maps AI-typical phrases → more natural alternatives (list = pick randomly)
PHRASE_MAP = {
    # Transitions / connectors
    r'\bfurthermore\b': ['Also', 'On top of that', 'Besides', 'What\'s more'],
    r'\bmoreover\b': ['Also', 'Beyond that', 'Not only that', 'Plus'],
    r'\bin addition\b': ['As well', 'On top of that', 'Also', 'And'],
    r'\bin conclusion\b': ['To wrap up', 'All in all', 'When you think about it', 'Ultimately'],
    r'\bto summarize\b': ['In short', 'Simply put', 'All things considered'],
    r'\bin summary\b': ['In short', 'To put it simply', 'Overall'],
    r'\bnotwithstanding\b': ['Even so', 'Despite that', 'Still'],
    r'\bsubsequently\b': ['Then', 'After that', 'Next'],
    r'\bnevertheless\b': ['Even so', 'Still', 'But'],
    r'\bconsequently\b': ['So', 'As a result', 'That\'s why'],
    r'\btherefore\b': ['So', 'That\'s why', 'Because of this'],
    r'\bhence\b': ['So', 'That\'s why', 'This means'],
    r'\bthus\b': ['So', 'As a result', 'Because of this'],

    # AI-typical openers
    r'\bit is (important|worth|crucial|essential|vital) to (note|mention|highlight|acknowledge|recognize) that\b':
        ['Keep in mind that', 'Worth noting:', 'One thing to consider is that', 'Something to keep in mind is that'],
    r'\bit is widely (known|recognized|acknowledged|accepted) that\b':
        ['Most people know that', 'It\'s pretty well known that', 'As most people know,'],
    r'\bit is (important|crucial|essential|vital) to\b':
        ['You need to', 'It really matters to', 'A key thing is to'],
    r'\bit is (undeniable|clear|evident|obvious) that\b':
        ['Clearly,', 'You can see that', 'No question,'],
    r'\bone must (consider|acknowledge|note|recognize)\b':
        ['It\'s worth thinking about', 'Consider this:', 'Think about'],
    r'\bone can (argue|see|observe)\b':
        ['You could argue', 'It seems', 'You can see'],

    # Hedging / academic bloat
    r'\bit is imperative that\b': ['We really need to', 'It\'s critical that'],
    r'\bdue to the fact that\b': ['because', 'since', 'given that'],
    r'\bin light of the fact that\b': ['since', 'because', 'given that'],
    r'\bwith regard to\b': ['about', 'when it comes to', 'on the topic of'],
    r'\bwith respect to\b': ['about', 'regarding', 'when it comes to'],
    r'\bin terms of\b': ['when it comes to', 'for', 'regarding'],
    r'\ba significant number of\b': ['many', 'a lot of', 'quite a few'],
    r'\ba large number of\b': ['many', 'lots of', 'plenty of'],
    r'\bthe majority of\b': ['most', 'most of', 'the bulk of'],
    r'\bprovide(s)? a (comprehensive|detailed|thorough)\b': ['give(s) a thorough', 'offer(s) a detailed'],
    r'\bplays? a (crucial|vital|key|important|significant) role in\b':
        ['matter(s) a lot for', 'is key to', 'shapes'],
    r'\bhas (been|have) shown to\b': ['tends to', 'seems to', 'often'],
    r'\bin the modern (world|era|age|society)\b': ['today', 'these days', 'now'],
    r'\bin today\'s (world|society|age|era)\b': ['these days', 'nowadays', 'today'],
    r'\bin the context of\b': ['when it comes to', 'in', 'within'],
    r'\bthe concept of\b': ['the idea of', '', 'the notion of'],

    # AI tell-tale words
    r'\butilize[sd]?\b': ['use', 'uses', 'used'],
    r'\butilization\b': ['use'],
    r'\bfacilitate[sd]?\b': ['help', 'make easier', 'support'],
    r'\bimplement[aion]+\b': ['use', 'putting into practice', 'applying'],
    r'\bdemonstrate[sd]?\b': ['show', 'shows', 'showed'],
    r'\benhance[sd]?\b': ['improve', 'boost', 'strengthen'],
    r'\boptimize[sd]?\b': ['improve', 'make better', 'fine-tune'],
    r'\bprioritize[sd]?\b': ['focus on', 'put first', 'make a priority'],
    r'\bleverage[sd]?\b': ['use', 'take advantage of', 'tap into'],
    r'\bsynergy\b': ['teamwork', 'collaboration', 'working together'],
    r'\bparadigm\b': ['model', 'approach', 'way of thinking'],
    r'\bpivotal\b': ['key', 'critical', 'really important'],
    r'\bcommendable\b': ['impressive', 'worth noting', 'good'],
    r'\bpropitious\b': ['good', 'favourable', 'promising'],
    r'\binextricably\b': ['closely', 'deeply'],
    r'\bpertaining to\b': ['about', 'related to', 'involving'],
    r'\bwithin the realm of\b': ['in', 'in the world of', 'when it comes to'],
    r'\bdelve into\b': ['look into', 'explore', 'dig into'],
    r'\bunpack\b': ['look at', 'explore', 'break down'],
    r'\brobust\b': ['strong', 'solid', 'reliable'],
    r'\bseamless(ly)?\b': ['smooth', 'easily', 'without issues'],
    r'\bcutting-edge\b': ['latest', 'advanced', 'new'],
    r'\bstate-of-the-art\b': ['latest', 'modern', 'advanced'],
    r'\bground-breaking\b': ['new', 'innovative', 'pioneering'],

    # Contractions (add naturalness)
    r'\bit is\b': ['it\'s'],
    r'\bthey are\b': ['they\'re'],
    r'\bwe are\b': ['we\'re'],
    r'\bthere is\b': ['there\'s'],
    r'\bthere are\b': ['there are'],  # keep as-is
    r'\bdo not\b': ['don\'t'],
    r'\bdoes not\b': ['doesn\'t'],
    r'\bcannot\b': ['can\'t'],
    r'\bwould not\b': ['wouldn\'t'],
    r'\bwill not\b': ['won\'t'],
    r'\bthat is\b': ['that\'s'],
    r'\bwhat is\b': ['what\'s'],
}

# Sentence starters that feel human
HUMAN_STARTERS = [
    'Honestly,', 'In reality,', 'The thing is,', 'Interestingly,',
    'As it turns out,', 'To be fair,', 'That said,', 'Of course,',
    'Here\'s the thing:', 'To put it simply,', 'Realistically,',
]


def _apply_phrase_substitutions(text: str) -> tuple[str, list[dict]]:
    """Apply phrase-level substitutions. Returns (new_text, changes_list)."""
    changes = []
    for pattern, replacements in PHRASE_MAP.items():
        if isinstance(replacements, list):
            replacement = random.choice(replacements)
        else:
            replacement = replacements

        # Only replace if match found
        matches_found = re.findall(pattern, text, flags=re.IGNORECASE)
        if matches_found:
            original_text = text
            # Preserve capitalisation of first letter
            def replace_fn(m):
                orig = m.group(0)
                rep = replacement
                if orig and orig[0].isupper() and rep:
                    rep = rep[0].upper() + rep[1:]
                return rep

            new_text = re.sub(pattern, replace_fn, text, flags=re.IGNORECASE)
            if new_text != original_text:
                changes.append({
                    'type': 'Phrase replacement',
                    'original': matches_found[0] if isinstance(matches_found[0], str) else ' '.join(matches_found[0]),
                    'replacement': replacement,
                })
                text = new_text

    return text, changes


def _vary_sentence_structure(text: str) -> tuple[str, list[dict]]:
    """Break very long sentences and add a human starter occasionally."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    changes = []
    new_sentences = []

    for i, sentence in enumerate(sentences):
        words = sentence.split()

        # Break overly long sentences (>40 words) at a conjunction
        if len(words) > 40:
            for conj in [', and ', ', but ', ', however ', ', although ', ', while ']:
                idx = sentence.find(conj)
                if idx > 20:
                    first = sentence[:idx].strip() + '.'
                    second = sentence[idx + len(conj):].strip()
                    if second:
                        second = second[0].upper() + second[1:]
                    new_sentences.extend([first, second])
                    changes.append({
                        'type': 'Sentence split',
                        'original': sentence[:60] + '...',
                        'replacement': 'Split into two shorter sentences',
                    })
                    break
            else:
                new_sentences.append(sentence)
        else:
            new_sentences.append(sentence)

    # Occasionally prepend a human-sounding sentence starter (max 1 per text)
    if new_sentences and len(new_sentences) >= 3:
        idx = min(2, len(new_sentences) - 1)
        starter = random.choice(HUMAN_STARTERS)
        original = new_sentences[idx]
        # Remove any leading caps since we're prepending
        new_sentences[idx] = f'{starter} {original[0].lower() + original[1:]}'
        changes.append({
            'type': 'Natural opener added',
            'original': original[:60],
            'replacement': new_sentences[idx][:60],
        })

    return ' '.join(new_sentences), changes


def _fix_spacing_and_punctuation(text: str) -> str:
    """Clean up any spacing issues introduced by substitutions."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s([,.!?;:])', r'\1', text)
    text = re.sub(r'([.!?])\s*([a-z])', lambda m: m.group(1) + ' ' + m.group(2).upper(), text)
    return text.strip()


# ── Main entry point ───────────────────────────────────────────────────────────

def humanize_text(text: str) -> dict:
    """
    Rewrite AI-generated text to sound more natural and human.

    Returns:
        {
          'humanized_text': str,
          'original_text': str,
          'changes_made': int,
          'changes': [{ type, original, replacement }],
          'readability_note': str,
        }
    """
    if not text or not text.strip():
        return {
            'humanized_text': '',
            'original_text': text,
            'changes_made': 0,
            'changes': [],
            'readability_note': 'No text provided.',
        }

    random.seed(42)  # Deterministic output
    all_changes = []

    # Step 1: phrase substitutions
    result, phrase_changes = _apply_phrase_substitutions(text)
    all_changes.extend(phrase_changes)

    # Step 2: sentence structure variation
    result, structure_changes = _vary_sentence_structure(result)
    all_changes.extend(structure_changes)

    # Step 3: cleanup
    result = _fix_spacing_and_punctuation(result)

    # Readability note
    word_count = len(result.split())
    if word_count < 50:
        note = 'Short text — humanization applied where possible.'
    elif all_changes:
        note = f'{len(all_changes)} changes applied to make the text sound more natural and less AI-generated.'
    else:
        note = 'Text already reads naturally — minimal changes needed.'

    return {
        'humanized_text': result,
        'original_text': text,
        'changes_made': len(all_changes),
        'changes': all_changes[:20],  # cap for display
        'readability_note': note,
    }
