from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from essays.models import Essay, EssayResult
from recommendations.engine import get_recommendations


class EssayReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        essay = get_object_or_404(Essay, pk=pk)
        if not request.user.is_teacher and essay.student != request.user:
            from rest_framework.response import Response
            return Response({'error': 'Unauthorized'}, status=403)

        result = get_object_or_404(EssayResult, essay=essay)
        recs   = get_recommendations(essay.student_id, result.problems or [])

        from .generator import generate_essay_report
        pdf_bytes = generate_essay_report(essay, result, essay.student, recommendations=recs)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="writewise_report_{pk}.pdf"'
        return response
