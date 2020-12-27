from django.urls import path, include
from . import views
from django.contrib import admin
from django.views.generic import TemplateView

urlpatterns = [
    # path('site/', , name='course_view'),
    # path('admin/', )
    path('api/', include([
        path('courses/', views.ObjectList.as_view()),
        path('course/<str:course>/', include([
            path('', views.CourseDetail.as_view()),
            path('enroll/', views.Enroll.as_view()),
            path('<str:topic>/<str:subtopic>/', views.SubTopicDetail.as_view()),
            path('rank/', views.Ranking.as_view())
        ]))
    ])),
    path('s/', TemplateView.as_view(template_name='index.html')),
    path('s/<path:resource>', TemplateView.as_view(template_name='index.html')),
]
