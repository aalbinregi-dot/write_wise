"""
Users app — Custom User model, Student/Teacher profiles, JWT auth
"""
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    STUDENT = 'student'
    TEACHER = 'teacher'
    ROLE_CHOICES = [(STUDENT, 'Student'), (TEACHER, 'Teacher')]

    email    = models.EmailField(unique=True)
    role     = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)
    course   = models.CharField(max_length=200, blank=True)
    bio      = models.TextField(blank=True)
    avatar   = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.role})'

    @property
    def is_student(self):
        return self.role == self.STUDENT

    @property
    def is_teacher(self):
        return self.role == self.TEACHER
