from django.urls import path
from .views import (
    EssayListCreateView, EssayDetailView, AnalyzeEssayView,
    EssayResultView, TeacherScoreOverrideView, StudentProgressView,
    ClassAnalyticsView, LearningProgressView, CompleteLessonView,
)

urlpatterns = [
    path('essays/',                               EssayListCreateView.as_view(),      name='essay-list'),
    path('essays/<uuid:pk>/',                     EssayDetailView.as_view(),          name='essay-detail'),
    path('essays/<uuid:pk>/analyze/',             AnalyzeEssayView.as_view(),         name='essay-analyze'),
    path('essays/<uuid:pk>/results/',             EssayResultView.as_view(),          name='essay-results'),
    path('essays/<uuid:pk>/override/',            TeacherScoreOverrideView.as_view(), name='essay-override'),
    path('students/<int:student_id>/progress/',   StudentProgressView.as_view(),      name='student-progress'),
    path('teacher/class-analytics/',              ClassAnalyticsView.as_view(),       name='class-analytics'),
    path('learning/progress/',                    LearningProgressView.as_view(),     name='learning-progress'),
    path('learning/<str:lesson_id>/complete/',    CompleteLessonView.as_view(),       name='lesson-complete'),
]
