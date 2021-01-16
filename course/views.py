from django.http.request import HttpHeaders
from django.http.response import HttpResponseForbidden
from judge.models import submission
from .models import Course, CourseParticipation, CourseSubmission, SubTopic, CourseProblem, Topic, CourseDevItem
from .serializers import CourseListSerializer, TopicSerializer, SubTopicSerializer, CourseProblemSerializer, CourseSerializer, CourseDevItemSerializer
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.views.generic.detail import DetailView
from django.utils.functional import cached_property
from django.utils import timezone
from judge.utils.opengraph import generate_opengraph
from django.conf import settings
from judge.models import Submission
from django.db.models import Case, Count, F, FloatField, IntegerField, Max, Min, Q, Sum, Value, When
from django.db.models.expressions import CombinedExpression
from collections import defaultdict, namedtuple
from functools import partial
from judge.utils.problems import _get_result_data
import json


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
            subtopic = SubTopicSerializer(topic.subtopics.filter(is_visible=True), many=True)
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
        courseprobelm = CourseProblem.objects.filter(course=self.course, subtopic=self.subtopic, is_visible=True)
        coursedevitem = CourseDevItem.objects.filter(course=self.course, subtopic=self.subtopic, is_visible=True)
        probelmserialized = CourseProblemSerializer(courseprobelm, many=True).data
        devitemserialized = CourseDevItemSerializer(coursedevitem, many=True).data
        
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
        
        for cd, ds in zip(coursedevitem, devitemserialized):
            ds['url'] = 'url'
            ds['name'] = cd.devitem.name
            ds['is_devitem'] = True

        serializersubtopic['problems'] = probelmserialized + devitemserialized
        
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
            course.user_count+=1
            course.save()
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
        cp = CourseParticipation.objects.values('score', 'user__user__username').filter(course=course, is_disqualified=False).order_by('-score', 'tiebreaker')
        if size != 'all':
            cp = cp[:int(size)]
        cp = list(cp)
        retd = {
            'other':cp
        }
        user = request.user
        if user.is_authenticated:
            myprofile = CourseParticipation.objects.filter(course=course, user=user.profile).values('score', 'user__user__username')
            print(myprofile)
            if myprofile.exists():
                myprofile = myprofile[0]
                retd['me'] = myprofile
                myprofile['username'] = myprofile['user__user__username']
                del myprofile['user__user__username']
        for c in cp:
            c['username'] = c['user__user__username']
            del c['user__user__username']
        
        return Response(retd)


class CourseMixin(object):
    context_object_name = 'course'
    model = Course
    slug_field = 'key'
    slug_url_kwarg = 'course'

    @cached_property
    def is_organizer(self):
        if not self.request.user.is_authenticated:
            return False
        return self.object.organizers.filter(id=self.request.profile.id).exists()

    @cached_property
    def can_edit(self):
        return self.object.is_editable_by(self.request.user)

    def get_context_data(self, **kwargs):
        context = super(CourseMixin, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['has_joined'] = self.has_joined

        context['now'] = timezone.now()
        context['is_organizer'] = self.is_organizer
        context['can_edit'] = self.can_edit

        if not self.object.og_image or not self.object.summary:
            metadata = generate_opengraph('generated-meta-contest:%d' % self.object.id,
                                          self.object.description, 'contest')
        context['meta_description'] = self.object.summary or metadata[0]
        context['og_image'] = self.object.og_image or metadata[1]
        context['has_moss_api_key'] = settings.MOSS_API_KEY is not None
        context['logo_override_image'] = self.object.logo_override_image
        if not context['logo_override_image'] and self.object.organizations.count() == 1:
            context['logo_override_image'] = self.object.organizations.first().logo_override_image

        return context

    def get_object(self, queryset=None):
        course = super(CourseMixin, self).get_object(queryset)

        profile = self.request.profile
        if profile:
            self.participation = CourseParticipation.objects.filter(course=course, user=profile)
        if (profile is not None and self.participation.exists()):
            self.has_joined = True
            return course

        # try:
        #     course.access_check(self.request.user)
        # except course.PrivateCourse:
        #     raise PrivateCourseError(course.name, course.is_private, course.is_organization_private,
        #                               course.organizations.all())
        # except Course.Inaccessible:
        #     raise Http404()
        # else:
        return course

    def dispatch(self, request, *args, **kwargs):
        try:
            return super(CourseMixin, self).dispatch(request, *args, **kwargs)
        except Http404:
            raise Http404


from django.utils.safestring import mark_safe
from judge.utils.stats import get_bar_chart, get_pie_chart


class CourseSubTopicStats(CourseMixin, DetailView):
    template_name = 'contest/stats.html'

    def get_title(self):
        return _('%s Statistics') % self.object.name

    def get_topic(self):
        topic = get_object_or_404(Topic, course=self.object, key=self.kwargs.get('topic'))
        self.topic_object = topic
        return topic
    
    def get_subtopic(self):
        topic = self.get_topic()
        subtopic = get_object_or_404(SubTopic, topic=topic, key=self.kwargs.get('subtopic'))
        self.subtopic_object = subtopic
        return subtopic
    
    def get_course_problems(self):
        self.course_problems_object = CourseProblem.objects.filter(subtopic=self.get_subtopic())
        return self.course_problems_object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.get_course_problems()
        queryset = Submission.objects.filter(course_problem_object=self.subtopic_object)

        ac_count = Count(Case(When(result='AC', then=Value(1)), output_field=IntegerField()))
        ac_rate = CombinedExpression(ac_count / Count('problem'), '*', Value(100.0), output_field=FloatField())

        status_count_queryset = list(
            queryset.values('problem__code', 'result').annotate(count=Count('result'))
                    .values_list('problem__code', 'result', 'count'),
        )
        labels, codes = [], []
        course_problems = self.course_problems_object.order_by('order').values_list('problem__name', 'problem__code')
        if course_problems:
            labels, codes = zip(*course_problems)
        num_problems = len(labels)
        status_counts = [[] for i in range(num_problems)]
        for problem_code, result, count in status_count_queryset:
            if problem_code in codes:
                status_counts[codes.index(problem_code)].append((result, count))

        result_data = defaultdict(partial(list, [0] * num_problems))
        for i in range(num_problems):
            for category in _get_result_data(defaultdict(int, status_counts[i]))['categories']:
                result_data[category['code']][i] = category['count']

        stats = {
            'problem_status_count': {
                'labels': labels,
                'datasets': [
                    {
                        'label': name,
                        'backgroundColor': settings.DMOJ_STATS_SUBMISSION_RESULT_COLORS[name],
                        'data': data,
                    }
                    for name, data in result_data.items()
                ],
            },
            'problem_ac_rate': get_bar_chart(
                queryset.values('course__problem__order', 'problem__name').annotate(ac_rate=ac_rate)
                        .order_by('course__problem__order').values_list('problem__name', 'ac_rate'),
            ),
            'language_count': get_pie_chart(
                queryset.values('language__name').annotate(count=Count('language__name'))
                        .filter(count__gt=0).order_by('-count').values_list('language__name', 'count'),
            ),
            'language_ac_rate': get_bar_chart(
                queryset.values('language__name').annotate(ac_rate=ac_rate)
                        .filter(ac_rate__gt=0).values_list('language__name', 'ac_rate'),
            ),
        }

        context['stats'] = mark_safe(json.dumps(stats))
        content['contest'] = self.object
        return context
