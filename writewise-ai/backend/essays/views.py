"""
Essay Views — submission, analysis, history, teacher override
"""
import sys
import io
import logging
from pathlib import Path
from datetime import datetime, timezone

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Essay, EssayResult, LearningProgress
from .serializers import EssaySerializer, EssayResultSerializer, LearningProgressSerializer
from users.models import User

logger = logging.getLogger(__name__)

# Add ml to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


class EssayListCreateView(generics.ListCreateAPIView):
    serializer_class = EssaySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            student_id = self.request.query_params.get('student_id')
            if student_id:
                return Essay.objects.filter(student_id=student_id)
            return Essay.objects.all()
        return Essay.objects.filter(student=user)

    def perform_create(self, serializer):
        essay = serializer.save(student=self.request.user)
        # Extract text from uploaded file if provided
        if essay.file_upload and not essay.essay_text.strip():
            essay.essay_text = _extract_text(essay.file_upload)
            essay.save()


class EssayDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = EssaySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_teacher:
            return Essay.objects.all()
        return Essay.objects.filter(student=self.request.user)


class AnalyzeEssayView(APIView):
    """Trigger full AI analysis for an essay."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        essay = get_object_or_404(Essay, pk=pk)
        if not request.user.is_teacher and essay.student != request.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        if not essay.essay_text or not essay.essay_text.strip():
            return Response({'error': 'Essay text is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        essay.status = 'analyzing'
        essay.save()

        try:
            # Get student history for personalized feedback
            history = list(
                EssayResult.objects.filter(essay__student=essay.student)
                .order_by('created_at')
                .values('predicted_score', 'grammar_error_count', 'spelling_error_count',
                        'vocab_diversity', 'readability_score')
            )

            from backend.analytics.analyzer import analyze_essay
            result_data = analyze_essay(essay.essay_text, student_history=history)

            if result_data.get('error'):
                essay.status = 'failed'
                essay.save()
                return Response({'error': result_data['error_message']}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            # Save/update result
            EssayResult.objects.update_or_create(
                essay=essay,
                defaults={
                    'predicted_score':      result_data['predicted_score'],
                    'final_score':          result_data['final_score'],
                    'score_confidence':     result_data['score_confidence'],
                    'previous_score':       result_data.get('previous_score'),
                    'word_count':           result_data['word_count'],
                    'sentence_count':       result_data['sentence_count'],
                    'paragraph_count':      result_data['paragraph_count'],
                    'grammar_error_count':  result_data['grammar_error_count'],
                    'spelling_error_count': result_data['spelling_error_count'],
                    'vocab_diversity':      result_data['vocab_diversity'],
                    'readability_score':    result_data['readability_score'],
                    'readability_grade':    result_data['readability_grade'],
                    'coherence_score':      result_data['coherence_score'],
                    'argument_score':       result_data['argument_score'],
                    'grammar_errors':       result_data['grammar_errors'],
                    'spelling_errors':      result_data['spelling_errors'],
                    'linguistic_features':  result_data['linguistic_features'],
                    'writing_analysis':     result_data['writing_analysis'],
                    'problems':             result_data['problems'],
                    'corrections':          result_data['corrections'],
                    'feedback':             result_data['feedback'],
                }
            )

            # Trigger recommendations
            _generate_recommendations(essay.student, result_data['problems'])

            essay.status = 'done'
            essay.analyzed_at = datetime.now(timezone.utc)
            essay.save()

            result = EssayResult.objects.get(essay=essay)
            return Response(EssayResultSerializer(result).data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(f'Analysis failed for essay {pk}: {e}')
            essay.status = 'failed'
            essay.save()
            return Response({'error': f'Analysis failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EssayResultView(generics.RetrieveAPIView):
    serializer_class = EssayResultSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        essay = get_object_or_404(Essay, pk=self.kwargs['pk'])
        if not self.request.user.is_teacher and essay.student != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied()
        return get_object_or_404(EssayResult, essay=essay)


class TeacherScoreOverrideView(APIView):
    """Allow teacher to override AI score."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_teacher:
            return Response({'error': 'Teachers only.'}, status=status.HTTP_403_FORBIDDEN)

        result = get_object_or_404(EssayResult, essay__pk=pk)
        teacher_score = request.data.get('teacher_score')

        if teacher_score is None or not (1 <= float(teacher_score) <= 6):
            return Response({'error': 'teacher_score must be between 1 and 6.'}, status=400)

        result.teacher_score = float(teacher_score)
        result.final_score   = float(teacher_score)
        result.save()

        essay = result.essay
        essay.model_version = f'{essay.model_version}+teacher'
        essay.save()

        return Response({
            'ai_score':      result.predicted_score,
            'teacher_score': result.teacher_score,
            'final_score':   result.final_score,
        })


class StudentProgressView(APIView):
    """Growth analytics for a student."""
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        if not request.user.is_teacher and request.user.id != int(student_id):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        results = (
            EssayResult.objects
            .filter(essay__student_id=student_id, essay__status='done')
            .order_by('essay__submitted_at')
            .values('essay__submitted_at', 'predicted_score', 'final_score',
                    'grammar_error_count', 'spelling_error_count',
                    'vocab_diversity', 'readability_score', 'word_count')
        )

        history = list(results)

        if not history:
            return Response({'history': [], 'summary': {}})

        scores   = [h['final_score']          for h in history if h['final_score']]
        grammar  = [h['grammar_error_count']  for h in history]
        spelling = [h['spelling_error_count'] for h in history]
        vocab    = [h['vocab_diversity']       for h in history if h['vocab_diversity']]

        summary = {
            'first_score':    scores[0]    if scores else None,
            'latest_score':   scores[-1]   if scores else None,
            'best_score':     max(scores)  if scores else None,
            'avg_score':      round(sum(scores) / len(scores), 2) if scores else None,
            'score_change':   round(scores[-1] - scores[0], 2) if len(scores) >= 2 else 0,
            'grammar_change': round(grammar[-1] - grammar[0], 2) if len(grammar) >= 2 else 0,
            'spelling_change':round(spelling[-1] - spelling[0], 2) if len(spelling) >= 2 else 0,
            'vocab_change':   round(vocab[-1] - vocab[0], 4) if len(vocab) >= 2 else 0,
            'total_essays':   len(history),
        }

        return Response({'history': history, 'summary': summary})


class ClassAnalyticsView(APIView):
    """Teacher class-wide analytics."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_teacher:
            return Response({'error': 'Teachers only.'}, status=status.HTTP_403_FORBIDDEN)

        from django.db.models import Avg, Count, Min, Max

        stats = EssayResult.objects.filter(essay__status='done').aggregate(
            avg_score=Avg('final_score'),
            min_score=Min('final_score'),
            max_score=Max('final_score'),
            total_essays=Count('id'),
        )

        students = User.objects.filter(role='student').count()

        # Score distribution
        from django.db.models import Case, When, IntegerField
        buckets = []
        for lo, hi, label in [(1, 2, '1-2'), (2, 3, '2-3'), (3, 4, '3-4'),
                               (4, 5, '4-5'), (5, 6, '5-6')]:
            count = EssayResult.objects.filter(
                essay__status='done',
                final_score__gte=lo,
                final_score__lt=hi + (0.01 if hi == 6 else 0)
            ).count()
            buckets.append({'range': label, 'count': count})

        return Response({
            'stats':           stats,
            'student_count':   students,
            'score_distribution': buckets,
        })


class LearningProgressView(generics.ListAPIView):
    serializer_class = LearningProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LearningProgress.objects.filter(student=self.request.user)


class CompleteLessonView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, lesson_id):
        progress, _ = LearningProgress.objects.get_or_create(
            student=request.user,
            lesson_id=lesson_id,
            defaults={'lesson_title': request.data.get('title', ''),
                      'lesson_category': request.data.get('category', '')}
        )
        progress.status = 'completed'
        progress.completed_at = datetime.now(timezone.utc)
        progress.save()
        return Response({'status': 'completed', 'lesson_id': lesson_id})


# ── Helpers ────────────────────────────────────────────────────────────────────

def _extract_text(file_field) -> str:
    """Extract plain text from uploaded file (PDF, DOCX, TXT)."""
    name = file_field.name.lower()
    content = b''
    try:
        content = file_field.read()
    except Exception:
        return ''

    if name.endswith('.txt'):
        return content.decode('utf-8', errors='replace')
    elif name.endswith('.pdf'):
        try:
            import fitz
            doc = fitz.open(stream=content, filetype='pdf')
            return '\n'.join(page.get_text() for page in doc)
        except Exception:
            return ''
    elif name.endswith('.docx'):
        try:
            import docx
            document = docx.Document(io.BytesIO(content))
            return '\n'.join(p.text for p in document.paragraphs)
        except Exception:
            return ''
    return ''


def _generate_recommendations(student, problems: list):
    """Map detected problems to lessons from knowledge graph."""
    try:
        from recommendations.engine import get_recommendations
        recommendations = get_recommendations(student.id, problems)
        for rec in recommendations[:5]:
            LearningProgress.objects.get_or_create(
                student=student,
                lesson_id=rec['lesson_id'],
                defaults={
                    'lesson_title':    rec['lesson'],
                    'lesson_category': rec['category'],
                    'status':          'recommended',
                }
            )
    except Exception as e:
        logger.warning(f'Recommendation generation failed: {e}')
