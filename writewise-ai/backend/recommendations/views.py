from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .engine import get_recommendations, get_all_lessons


class RecommendationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id=None):
        from essays.models import EssayResult
        from essays.models import Essay

        target = student_id or request.user.id
        if not request.user.is_teacher and request.user.id != int(target):
            return Response({'error': 'Unauthorized'}, status=403)

        # Get problems from latest completed essay
        latest = (EssayResult.objects
                  .filter(essay__student_id=target, essay__status='done')
                  .order_by('-created_at')
                  .first())

        problems = latest.problems if latest else []
        recommendations = get_recommendations(target, problems)
        return Response({'recommendations': recommendations, 'based_on_essay': str(latest.essay_id) if latest else None})


class LessonsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        category = request.query_params.get('category')
        lessons  = get_all_lessons(category=category)
        return Response({'lessons': lessons, 'count': len(lessons)})
