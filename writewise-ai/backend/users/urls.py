from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LoginView, ProfileView, StudentListView, StudentDetailView

urlpatterns = [
    path('register/',             RegisterView.as_view(),      name='auth-register'),
    path('login/',                LoginView.as_view(),         name='auth-login'),
    path('refresh/',              TokenRefreshView.as_view(),  name='auth-refresh'),
    path('me/',                   ProfileView.as_view(),       name='auth-profile'),
    path('teacher/students/',     StudentListView.as_view(),   name='teacher-students'),
    path('teacher/students/<int:pk>/', StudentDetailView.as_view(), name='student-detail'),
]
