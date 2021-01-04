from django.http.request import HttpHeaders
from django.http.response import HttpResponseForbidden
from judge.models import submission
from .models import Course, CourseParticipation, CourseSubmission, SubTopic, CourseProblem, Topic
from .serializers import CourseListSerializer, TopicSerializer, SubTopicSerializer, CourseProblemSerializer, CourseSerializer
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404


class ObjectList(APIView):
    model = Course
    serializer_class = CourseListSerializer

    def get_queryset(self):
        return self.model.get_visible(self.request.user)

    def get(self, request, format=None):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True).data
        profile = request.user.profile if request.user.is_authenticated else None
        if profile:
            for c, cs in zip(queryset, serializer):
                cs['enrolled'] = c.users.filter(user=profile).exists()

        return Response(serializer)

    # def post(self, request, format=None):
    #     serializer = SnippetSerializer(data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseDetail(APIView):
    model = Course
    slug_field = 'key'
    slug_url_kwarg = 'course'
    serializer_class = CourseSerializer

    def get_object(self):
        return get_object_or_404(self.model, key=self.kwargs.get(self.slug_url_kwarg))

    def get(self, request, *args, **kwargs):
        # print(self.args, self.kwargs)
        course = self.get_object()
        
        if not course.is_accessible_by(request.user):
            raise Http404()
        
        serializercourse = self.serializer_class(course).data
        topics = course.topic_set.filter(is_visible=True)
        serializertopic = TopicSerializer(topics, many=True).data
        
        for topic, serialized in zip(topics, serializertopic):
            subtopic = SubTopicSerializer(topic.subtopic_set.filter(is_visible=True), many=True)
            serialized['subtopics'] = subtopic.data

        serializercourse['topics'] = serializertopic
        return Response(serializercourse)


class SubTopicDetail(APIView):
    model = SubTopic
    serializer_class = SubTopicSerializer
    slug_field = 'key'
    slug_url_kwarg = 'subtopic'
    slug_url_kwarg_course = 'course'
    slug_url_kwarg_topic = 'topic'
    
    def get_course_object(self):
        return get_object_or_404(Course, key = self.kwargs.get(self.slug_url_kwarg_course))
    
    def get_topic_object(self):
        return get_object_or_404(Topic, course=self.course, key = self.kwargs.get(self.slug_url_kwarg_topic))
    
    def get_object(self):
        return get_object_or_404(SubTopic, topic = self.topic, key = self.kwargs.get(self.slug_url_kwarg))
    
    def get(self, request, *args, **kwargs):
        self.course = self.get_course_object()
        
        if not self.course.is_accessible_by(request.user):
            raise Http404()

        self.topic = self.get_topic_object()
        if not self.topic.is_visible:
            raise Http404()
        self.subtopic = self.get_object()

        serializersubtopic = self.serializer_class(self.subtopic).data
        courseprobelm = CourseProblem.objects.filter(course=self.course, subtopic=self.subtopic)
        probelmserialized = CourseProblemSerializer(courseprobelm, many=True).data
        user = request.user

        if user.is_anonymous:
            course_profile = None
        else:
            profile = user.profile
            course_profiles = self.course.users.filter(user=profile)
            if course_profiles.exists():
                course_profile = course_profiles.first()
            else:
                course_profile = None

        for cp, ps in zip(courseprobelm, probelmserialized):
            ps['url'] = cp.problem.get_absolute_url()+'/c/'+self.course.key
            ps['name'] = cp.problem.name
            if course_profile:
                submissions = course_profile.submissions
                if submissions.exists():
                    solved = submissions.filter(problem=cp, submission__result='AC').exists()
                    ps['result'] = solved
                

        serializersubtopic['problems'] = probelmserialized
        
        return Response(serializersubtopic)

class Enroll(APIView):
    model = Course
    slug_url_kwarg = 'course'

    def get_course_object(self):
        return get_object_or_404(self.model, key=self.kwargs.get(self.slug_url_kwarg))

    def get(self, request, *args, **kwargs):
        user = request.user
        course = self.get_course_object()
        if course.can_join(user):
            course_profile, created = CourseParticipation.objects.get_or_create(course = course, user=user.profile)
            return Response(status=status.HTTP_201_CREATED)
        if user.is_anonymous:
            return HttpResponseForbidden('U need to Sign up')
        return HttpResponseForbidden('This course is Not for U')


class Ranking(APIView):
    model = Course
    slug_url_kwarg = 'course'

    def get_course_object(self):
        return get_object_or_404(self.model, key=self.kwargs.get(self.slug_url_kwarg))

    def get(self, request, *args, **kwargs):
        course = self.get_course_object()
        size = request.GET.get('size', 20) # else 20
        print(size)
        cp = CourseParticipation.objects.values('score', 'user__user__username').filter(course=course, is_disqualified=False).order_by('-score')
        if size != 'all':
            cp = cp[:int(size)]
        cp = list(cp)
        for c in cp:
            c['username'] = c['user__user__username']
            del c['user__user__username']
        return Response(cp)


