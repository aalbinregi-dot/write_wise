"""
Tools Views — Plagiarism Check & AI Humanizer endpoints
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .plagiarism import check_plagiarism
from .humanizer import humanize_text


class PlagiarismCheckView(APIView):
    """POST /api/tools/plagiarism/ — check text for plagiarism."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get('text', '').strip()
        if not text:
            return Response({'error': 'No text provided.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(text.split()) < 10:
            return Response({'error': 'Please provide at least 10 words.'}, status=status.HTTP_400_BAD_REQUEST)

        result = check_plagiarism(text)
        return Response(result, status=status.HTTP_200_OK)


class HumanizerView(APIView):
    """POST /api/tools/humanize/ — rewrite AI text to sound human."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get('text', '').strip()
        if not text:
            return Response({'error': 'No text provided.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(text.split()) < 5:
            return Response({'error': 'Please provide at least 5 words.'}, status=status.HTTP_400_BAD_REQUEST)

        result = humanize_text(text)
        return Response(result, status=status.HTTP_200_OK)
