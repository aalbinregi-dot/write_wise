from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class WritingAnalyticsView(APIView):
    """Return writing analytics summary for a student."""
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id=None):
        from essays.models import EssayResult

        target = student_id or request.user.id
        if not request.user.is_teacher and request.user.id != int(target):
            return Response({'error': 'Unauthorized'}, status=403)

        results = (
            EssayResult.objects
            .filter(essay__student_id=target, essay__status='done')
            .order_by('essay__submitted_at')
            .values(
                'essay__id', 'essay__submitted_at', 'essay__title',
                'predicted_score', 'final_score',
                'grammar_error_count', 'spelling_error_count',
                'vocab_diversity', 'readability_score',
                'coherence_score', 'argument_score', 'word_count',
            )
        )

        history = list(results)

        if not history:
            return Response({'history': [], 'comparison': None, 'strengths': [], 'weaknesses': []})

        # Strengths and weaknesses from latest essay
        latest = history[-1]
        strengths, weaknesses = _classify_strengths(latest)

        # Before vs After
        comparison = None
        if len(history) >= 2:
            first  = history[0]
            last   = history[-1]
            comparison = {
                'first_essay':  {'date': first['essay__submitted_at'], 'score': first['final_score'],
                                 'grammar_errors': first['grammar_error_count'],
                                 'spelling_errors': first['spelling_error_count'],
                                 'vocab_diversity': first['vocab_diversity'],
                                 'word_count': first['word_count']},
                'latest_essay': {'date': last['essay__submitted_at'],  'score': last['final_score'],
                                 'grammar_errors': last['grammar_error_count'],
                                 'spelling_errors': last['spelling_error_count'],
                                 'vocab_diversity': last['vocab_diversity'],
                                 'word_count': last['word_count']},
                'improvements': {
                    'score':   _pct_change(first['final_score'], last['final_score']),
                    'grammar': _pct_change(first['grammar_error_count'], last['grammar_error_count'], invert=True),
                    'spelling':_pct_change(first['spelling_error_count'], last['spelling_error_count'], invert=True),
                    'vocab':   _pct_change(first['vocab_diversity'], last['vocab_diversity']),
                },
            }

        return Response({
            'history':    history,
            'comparison': comparison,
            'strengths':  strengths,
            'weaknesses': weaknesses,
        })


def _classify_strengths(result: dict) -> tuple:
    strengths, weaknesses = [], []
    score = result.get('final_score') or 0

    if (result.get('spelling_error_count') or 0) <= 1: strengths.append('Spelling')
    else: weaknesses.append('Spelling')

    if (result.get('grammar_error_count') or 0) <= 2: strengths.append('Grammar')
    else: weaknesses.append('Grammar')

    ttr = result.get('vocab_diversity') or 0
    if ttr >= 0.45: strengths.append('Vocabulary')
    else: weaknesses.append('Vocabulary')

    if score >= 4.5: strengths.append('Overall Writing Quality')

    return strengths, weaknesses


def _pct_change(old, new, invert=False) -> str:
    if old is None or new is None or old == 0:
        return '—'
    change = ((new - old) / abs(old)) * 100
    if invert:
        change = -change
    sign = '+' if change >= 0 else ''
    return f'{sign}{change:.1f}%'
