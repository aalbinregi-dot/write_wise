from rest_framework import serializers
from .models import Essay, EssayResult, LearningProgress


class EssaySerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    has_result   = serializers.SerializerMethodField()

    class Meta:
        model  = Essay
        fields = ['id', 'title', 'essay_text', 'file_upload', 'status',
                  'submitted_at', 'analyzed_at', 'model_version',
                  'student', 'student_name', 'has_result']
        read_only_fields = ['id', 'status', 'submitted_at', 'analyzed_at',
                            'model_version', 'student', 'student_name', 'has_result']

    def get_student_name(self, obj):
        return obj.student.get_full_name() or obj.student.username

    def get_has_result(self, obj):
        return hasattr(obj, 'result')


class EssayResultSerializer(serializers.ModelSerializer):
    score_label = serializers.SerializerMethodField()

    class Meta:
        model  = EssayResult
        fields = '__all__'

    def get_score_label(self, obj):
        score = obj.final_score or obj.predicted_score or 0
        if score >= 5.5:  return 'Excellent'
        if score >= 4.5:  return 'Good'
        if score >= 3.5:  return 'Satisfactory'
        if score >= 2.5:  return 'Developing'
        return 'Beginning'


class LearningProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LearningProgress
        fields = ['id', 'lesson_id', 'lesson_title', 'lesson_category',
                  'status', 'started_at', 'completed_at']
