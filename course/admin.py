from django.contrib import admin
from .models import Course, Topic, SubTopic, CourseProblem, CourseSubmission, CourseParticipation
# Register your models here.

admin.site.register(Course)
admin.site.register(Topic)
admin.site.register(SubTopic)
admin.site.register(CourseProblem)
admin.site.register(CourseSubmission)
admin.site.register(CourseParticipation)