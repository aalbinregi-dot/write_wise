"""
Essays app — submission, storage, history, file parsing, full analysis orchestration
"""
import uuid
from django.db import models
from django.conf import settings


class Essay(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('analyzing', 'Analyzing'),
        ('done',      'Done'),
        ('failed',    'Failed'),
    ]

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student        = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                       related_name='essays')
    title          = models.CharField(max_length=300, blank=True)
    essay_text     = models.TextField()
    file_upload    = models.FileField(upload_to='essays/', null=True, blank=True)
    status         = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    submitted_at   = models.DateTimeField(auto_now_add=True)
    analyzed_at    = models.DateTimeField(null=True, blank=True)
    model_version  = models.CharField(max_length=50, default='1.0.0')

    class Meta:
        db_table = 'essays'
        ordering = ['-submitted_at']

    def __str__(self):
        return f'Essay {self.id} by {self.student}'


class EssayResult(models.Model):
    essay              = models.OneToOneField(Essay, on_delete=models.CASCADE,
                                               related_name='result')
    # Scores
    predicted_score    = models.FloatField(null=True)
    teacher_score      = models.FloatField(null=True, blank=True)
    final_score        = models.FloatField(null=True)
    score_confidence   = models.FloatField(null=True)
    previous_score     = models.FloatField(null=True, blank=True)

    # Counts
    word_count         = models.IntegerField(default=0)
    sentence_count     = models.IntegerField(default=0)
    paragraph_count    = models.IntegerField(default=0)
    grammar_error_count   = models.IntegerField(default=0)
    spelling_error_count  = models.IntegerField(default=0)

    # Metrics
    vocab_diversity    = models.FloatField(null=True)
    readability_score  = models.FloatField(null=True)
    readability_grade  = models.CharField(max_length=50, blank=True)
    coherence_score    = models.FloatField(null=True)
    argument_score     = models.FloatField(null=True)

    # JSON blobs
    grammar_errors     = models.JSONField(default=list)
    spelling_errors    = models.JSONField(default=list)
    linguistic_features = models.JSONField(default=dict)
    writing_analysis   = models.JSONField(default=dict)
    problems           = models.JSONField(default=list)
    corrections        = models.JSONField(default=list)
    feedback           = models.JSONField(default=dict)
    recommendations    = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'essay_results'

    def __str__(self):
        return f'Result for essay {self.essay_id}'


class LearningProgress(models.Model):
    student         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                        related_name='learning_progress')
    lesson_id       = models.CharField(max_length=20)
    lesson_title    = models.CharField(max_length=300)
    lesson_category = models.CharField(max_length=50)
    status          = models.CharField(max_length=20, default='recommended',
                                       choices=[('recommended','Recommended'),
                                                ('started','Started'),
                                                ('completed','Completed')])
    started_at      = models.DateTimeField(null=True, blank=True)
    completed_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'learning_progress'
        unique_together = ['student', 'lesson_id']
