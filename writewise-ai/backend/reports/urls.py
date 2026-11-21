from django.urls import path
from .views import EssayReportView

urlpatterns = [
    path('essays/<uuid:pk>/report/', EssayReportView.as_view(), name='essay-report'),
]
