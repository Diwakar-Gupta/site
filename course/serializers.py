from .models import Course, CourseProblem, Topic, SubTopic
from judge.models import Problem
from rest_framework import serializers


class ProblemListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseProblem
        fields = ['code', 'name']


class CourseProblemSerializer(serializers.ModelSerializer):
    problem = ProblemListSerializer

    class Meta:
        model = CourseProblem
        fields = ['points', 'order']


class SubTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['key', 'name', 'order']


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['key', 'name', 'order']


class CourseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['key', 'name', 'is_private', 'user_count', 'is_locked', 'is_visible']
