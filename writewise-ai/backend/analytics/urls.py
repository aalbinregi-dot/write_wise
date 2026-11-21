from django.urls import path
from .views import WritingAnalyticsView

urlpatterns = [
    path('students/<int:student_id>/analytics/', WritingAnalyticsView.as_view(), name='student-analytics'),
    path('analytics/me/', WritingAnalyticsView.as_view(), name='my-analytics'),
]
