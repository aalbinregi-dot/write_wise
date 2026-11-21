from django.urls import path
from .views import RecommendationsView, LessonsView

urlpatterns = [
    path('students/<int:student_id>/recommendations/', RecommendationsView.as_view(), name='recommendations'),
    path('lessons/', LessonsView.as_view(), name='lessons'),
]
