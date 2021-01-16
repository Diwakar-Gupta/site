from django.contrib import admin
from .models import Course, Topic, SubTopic, DevItem, CourseDevItem, CourseProblem, CourseSubmission, CourseParticipation
# Register your models here.

admin.site.register(DevItem)
admin.site.register(CourseDevItem)
admin.site.register(CourseProblem)
admin.site.register(CourseSubmission)
admin.site.register(CourseParticipation)

class CourseProblemInline(admin.TabularInline):
    model = CourseProblem
    exclude = ['course']

class CourseDevItemInline(admin.TabularInline):
    model = CourseDevItem
    exclude = ['course']
    
class SubTopicAdmin(admin.ModelAdmin):
    inlines = [
        CourseProblemInline,
        CourseDevItemInline
    ]

admin.site.register(SubTopic, SubTopicAdmin)

class SubTopicInline(admin.TabularInline):
    model = SubTopic
    show_change_link = True

class TopicAdmin(admin.ModelAdmin):
    inlines = [
        SubTopicInline,
    ]

admin.site.register(Topic, TopicAdmin)


class TopicInline(admin.TabularInline):
    model = Topic
    show_change_link = True

class CourseAdmin(admin.ModelAdmin):
    inlines = [
        TopicInline,
    ]

admin.site.register(Course, CourseAdmin)
