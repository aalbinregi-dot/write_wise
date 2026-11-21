from django.urls import path
from .views import PlagiarismCheckView, HumanizerView

urlpatterns = [
    path('plagiarism/', PlagiarismCheckView.as_view(), name='plagiarism-check'),
    path('humanize/',   HumanizerView.as_view(),       name='ai-humanize'),
]
