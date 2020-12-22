from django.urls import path, include
from . import views
from django.contrib import admin

urlpatterns = [
    # path('site/', , name='course_view'),
    # path('admin/', )
    path('api/', include([
        path('courses/', views.ObjectList.as_view()),
        path('course/<str:course>/', include([
            path('', views.CourseDetail.as_view()),
            path('enroll/', views.Enroll.as_view()),
            path('<str:topic>/<str:subtopic>/', views.SubTopicDetail.as_view())
        ]))
    ])),
]