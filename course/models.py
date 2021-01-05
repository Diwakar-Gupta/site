from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models, transaction
from django.db.models import CASCADE, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext, gettext_lazy as _
from jsonfield import JSONField
from lupa import LuaRuntime
from moss import MOSS_LANG_C, MOSS_LANG_CC, MOSS_LANG_JAVA, MOSS_LANG_PYTHON

# from judge import contest_format
from judge.models.problem import Problem
from judge.models.profile import Organization, Profile
from judge.models.submission import Submission
# from judge.ratings import rate_course

__all__ = ['Course', 'Topic','SubTopic', 'CourseParticipation', 'CourseProblem', 'CourseSubmission']


class MinValueOrNoneValidator(MinValueValidator):
    def compare(self, a, b):
        return a is not None and b is not None and super().compare(a, b)


# class courseTag(models.Model):
#     color_validator = RegexValidator('^#(?:[A-Fa-f0-9]{3}){1,2}$', _('Invalid colour.'))

#     name = models.CharField(max_length=20, verbose_name=_('tag name'), unique=True,
#                             validators=[RegexValidator(r'^[a-z-]+$', message=_('Lowercase letters and hyphens only.'))])
#     color = models.CharField(max_length=7, verbose_name=_('tag colour'), validators=[color_validator])
#     description = models.TextField(verbose_name=_('tag description'), blank=True)

#     def __str__(self):
#         return self.name

#     def get_absolute_url(self):
#         return reverse('course_tag', args=[self.name])

#     @property
#     def text_color(self, cache={}):
#         if self.color not in cache:
#             if len(self.color) == 4:
#                 r, g, b = [ord(bytes.fromhex(i * 2)) for i in self.color[1:]]
#             else:
#                 r, g, b = [i for i in bytes.fromhex(self.color[1:])]
#             cache[self.color] = '#000' if 299 * r + 587 * g + 144 * b > 140000 else '#fff'
#         return cache[self.color]

#     class Meta:
#         verbose_name = _('course tag')
#         verbose_name_plural = _('course tags')


class Course(models.Model):
    key = models.CharField(max_length=20, verbose_name=_('course id'), unique=True,
                           validators=[RegexValidator('^[a-z0-9]+$', _('course id must be ^[a-z0-9]+$'))])
    name = models.CharField(max_length=100, verbose_name=_('course name'), db_index=True)
    organizers = models.ManyToManyField(Profile, help_text=_('These people will be able to edit the course.'),
                                        related_name='organizers+')
    description = models.TextField(verbose_name=_('description'), blank=True)
    problems = models.ManyToManyField(Problem, verbose_name=_('problems'), through='CourseProblem')
    #start_time = models.DateTimeField(verbose_name=_('start time'), db_index=True)
    # time_limit = models.DurationField(verbose_name=_('time limit'), blank=True, null=True)
    is_visible = models.BooleanField(verbose_name=_('publicly visible'), default=False,
                                     help_text=_('Should be set even for organization-private courses, where it '
                                                 'determines whether the course is visible to members of the '
                                                 'specified organizations.'))
    is_rated = models.BooleanField(verbose_name=_('course rated'), help_text=_('Whether this course can be rated.'),
                                   default=False)
    hide_scoreboard = models.BooleanField(verbose_name=_('hide scoreboard'),
                                          help_text=_('Whether the scoreboard should remain hidden for the duration '
                                                      'of the course.'),
                                          default=False)
    view_course_scoreboard = models.ManyToManyField(Profile, verbose_name=_('view course scoreboard'), blank=True,
                                                     related_name='view_course_scoreboard',
                                                     help_text=_('These users will be able to view the scoreboard.'))
    use_clarifications = models.BooleanField(verbose_name=_('no comments'),
                                             help_text=_("Use clarification system instead of comments."),
                                             default=True)
    # rating_floor = models.IntegerField(verbose_name=('rating floor'), help_text=_('Rating floor for course'),
    #                                    null=True, blank=True)
    # rating_ceiling = models.IntegerField(verbose_name=('rating ceiling'), help_text=_('Rating ceiling for course'),
    #                                      null=True, blank=True)
    # rate_all = models.BooleanField(verbose_name=_('rate all'), help_text=_('Rate all users who joined.'), default=False)
    # rate_exclude = models.ManyToManyField(Profile, verbose_name=_('exclude from ratings'), blank=True,
    #                                       related_name='rate_exclude+')
    is_private = models.BooleanField(verbose_name=_('private to specific users'), default=False)
    private_courseants = models.ManyToManyField(Profile, blank=True, verbose_name=_('private courseants'),
                                                 help_text=_('If private, only these users may see the course'),
                                                 related_name='private_courseants+')
    hide_problem_tags = models.BooleanField(verbose_name=_('hide problem tags'),
                                            help_text=_('Whether problem tags should be hidden by default.'),
                                            default=False)
    run_pretests_only = models.BooleanField(verbose_name=_('run pretests only'),
                                            help_text=_('Whether judges should grade pretests only, versus all '
                                                        'testcases. Commonly set during a course, then unset '
                                                        'prior to rejudging user submissions when the course ends.'),
                                            default=False)
    is_organization_private = models.BooleanField(verbose_name=_('private to organizations'), default=False)
    organizations = models.ManyToManyField(Organization, blank=True, verbose_name=_('organizations'),
                                           help_text=_('If private, only these organizations may see the course'))
    og_image = models.CharField(verbose_name=_('OpenGraph image'), default='', max_length=150, blank=True)
    logo_override_image = models.CharField(verbose_name=_('Logo override image'), default='', max_length=150,
                                           blank=True,
                                           help_text=_('This image will replace the default site logo for users '
                                                       'inside the course.'))
    user_count = models.IntegerField(verbose_name=_('the amount of live participants'), default=0)
    summary = models.TextField(blank=True, verbose_name=_('course summary'),
                               help_text=_('Plain-text, shown in meta description tag, e.g. for social media.'))
    access_code = models.CharField(verbose_name=_('access code'), blank=True, default='', max_length=255,
                                   help_text=_('An optional code to prompt courseants before they are allowed '
                                               'to join the course. Leave it blank to disable.'))
    banned_users = models.ManyToManyField(Profile, verbose_name=_('personae non gratae'), blank=True,
                                          help_text=_('Bans the selected users from joining this course.'))
    # format_name = models.CharField(verbose_name=_('course format'), default='default', max_length=32,
    #                                choices=contest_format.choices(), help_text=_('The course format module to use.'))
    # format_config = JSONField(verbose_name=_('course format configuration'), null=True, blank=True,
    #                           help_text=_('A JSON object to serve as the configuration for the chosen course format '
    #                                       'module. Leave empty to use None. Exact format depends on the course format '
    #                                       'selected.'))
    problem_label_script = models.TextField(verbose_name='course problem label script', blank=True,
                                            help_text='A custom Lua function to generate problem labels. Requires a '
                                                      'single function with an integer parameter, the zero-indexed '
                                                      'course problem index, and returns a string, the label.')
    is_locked = models.BooleanField(verbose_name=_('course lock'), default=False,
                                    help_text=_('Prevent submissions from this course from being rejudged.'))
    is_user_enroll_locked = models.BooleanField(verbose_name=_('course enroll lock'), default=False,
                                    help_text=_('Prevent user Enroll from this course.'))
    points_precision = models.IntegerField(verbose_name=_('precision points'), default=3,
                                           validators=[MinValueValidator(0), MaxValueValidator(10)],
                                           help_text=_('Number of digits to round points to.'))

    # @cached_property
    # def format_class(self):
        # return course_format.formats[self.format_name]

    # @cached_property
    # def format(self):
        # return self.format_class(self, self.format_config)
    
    def __str__(self) -> str:
        return self.name

    @cached_property
    def get_label_for_problem(self):
        if not self.problem_label_script:
            return self.format.get_label_for_problem

        def DENY_ALL(obj, attr_name, is_setting):
            raise AttributeError()
        lua = LuaRuntime(attribute_filter=DENY_ALL, register_eval=False, register_builtins=False)
        return lua.eval(self.problem_label_script)

    def clean(self):
        pass
        # Django will complain if you didn't fill in start_time or end_time, so we don't have to.
        # if self.start_time and self.end_time and self.start_time >= self.end_time:
        #     raise ValidationError('What is this? A course that ended before it starts?')
        # self.format_class.validate(self.format_config)

        # try:
        #     # a course should have at least one problem, with course problem index 0
        #     # so test it to see if the script returns a valid label.
        #     label = self.get_label_for_problem(0)
        # except Exception as e:
        #     raise ValidationError('course problem label script: %s' % e)
        # else:
        #     if not isinstance(label, str):
        #         raise ValidationError('course problem label script: script should return a string.')

    def is_in_course(self, user):
        if user.is_authenticated:
            profile = user.profile
            return profile and profile.current_course is not None and profile.current_course.course == self
        return False

    def can_see_own_scoreboard(self, user):
        if self.can_see_full_scoreboard(user):
            return True
        if not self.can_join:
            return False
        if not self.show_scoreboard and not self.is_in_course(user):
            return False
        return True

    def can_see_full_scoreboard(self, user):
        if self.show_scoreboard:
            return True
        if user.has_perm('judge.see_private_course'):
            return True
        if self.is_editable_by(user):
            return True
        if user.is_authenticated and self.view_course_scoreboard.filter(id=user.profile.id).exists():
            return True
        return False

    @cached_property
    def show_scoreboard(self):
        if not self.can_join:
            return False
        if self.hide_scoreboard and not self.ended:
            return False
        return True

    @property
    def course_window_length(self):
        return self.end_time - self.start_time

    @cached_property
    def _now(self):
        # This ensures that all methods talk about the same now.
        return timezone.now()

    # @cached_property
    def can_join(self, user):
        if (not user.is_authenticated) or self.is_user_enroll_locked or self.is_locked:
            return False
        is_banned = self.banned_users.filter(id = user.profile.id).exists()
        if is_banned :
            return False
        
        if user.is_authenticated:
            in_users = self.private_courseants.filter(id=user.profile.id).exists()
            in_org = self.organizations.filter(id__in=user.profile.organizations.all()).exists()
        else:
            return False
        
        if self.is_private:
            if in_users:
                return True
            else:
                return False
        if self.is_organization_private:
            if in_org:
                return True
            else:
                return False
        return True

    # @property
    # def time_before_start(self):
    #     if self.start_time >= self._now:
    #         return self.start_time - self._now
    #     else:
    #         return None

    # @property
    # def time_before_end(self):
    #     if self.end_time >= self._now:
    #         return self.end_time - self._now
    #     else:
    #         return None

    # @cached_property
    # def ended(self):
    #     return self.end_time < self._now

    # def __str__(self):
    #     return self.name

    # def get_absolute_url(self):
        # return reverse('course_view', args=(self.key,))

    def update_user_count(self):
        self.user_count = self.users.count()
        self.save()

    update_user_count.alters_data = True

    class Inaccessible(Exception):
        pass

    class PrivateCourse(Exception):
        pass

    def can_submit(self, user):
        if not user.is_authenticated:
            return False
        is_banned = self.banned_users.filter(id = user.profile.id).exists()
        if is_banned or self.is_locked:
            return False
        return True

    def access_check(self, user):
        # If the user can view all courses
        if user.has_perm('course.see_private_course'):
            return

        # User can edit the course
        if self.is_editable_by(user):
            return

        # course is not publicly visible
        if not self.is_visible:
            raise self.Inaccessible()

        # course is not private
        if not self.is_private and not self.is_organization_private:
            return

        if user.is_authenticated:
            if self.view_course_scoreboard.filter(id=user.profile.id).exists():
                return

            in_org = self.organizations.filter(id__in=user.profile.organizations.all()).exists()
            in_users = self.private_courseants.filter(id=user.profile.id).exists()
        else:
            in_org = False
            in_users = False

        if not self.is_private and self.is_organization_private:
            if in_org:
                return
            raise self.PrivateCourse()

        if self.is_private and not self.is_organization_private:
            if in_users:
                return
            raise self.PrivateCourse()

        if self.is_private and self.is_organization_private:
            if in_org and in_users:
                return
            raise self.PrivateCourse()

    def is_accessible_by(self, user):
        try:
            self.access_check(user)
        except (self.Inaccessible, self.PrivateCourse):
            return False
        else:
            return True

    def is_visible_for(self, user):
        # course is not publicly visible
        if self.is_visible:
            return True
        
        # If the user can view all courses
        if user.has_perm('course.see_private_course'):
            return True

        # User can edit the course
        if self.is_editable_by(user):
            return True

        # course is private
        # if self.is_private and not self.is_organization_private:
        #     return

        if user.is_authenticated:
            in_org = self.organizations.filter(id__in=user.profile.organizations.all()).exists()
            in_users = self.private_courseants.filter(id=user.profile.id).exists()
        else:
            in_org = False
            in_users = False

        if not self.is_private and self.is_organization_private:
            return in_org

        if self.is_private and not self.is_organization_private:
            return in_users

        if self.is_private and self.is_organization_private:
            return in_org and in_users

        return False


    def is_editable_by(self, user):
        # If the user can edit all courses
        if user.has_perm('judge.edit_all_course'):
            return True

        # If the user is a course organizer
        if user.has_perm('judge.edit_own_course') and \
                self.organizers.filter(id=user.profile.id).exists():
            return True

        return False

    @classmethod
    def get_visible(cls, user):
        if not user.is_authenticated:
            return cls.objects.filter(is_visible=True, is_organization_private=False, is_private=False) \
                              .defer('description').distinct()

        queryset = cls.objects.defer('description')
        if not (user.has_perm('course.see_private_course') or user.has_perm('course.edit_all_course')):
            q = Q(is_visible=True)
            q &= (
                Q(view_course_scoreboard=user.profile) |
                Q(is_organization_private=False, is_private=False) |
                Q(is_organization_private=False, is_private=True, private_courseants=user.profile) |
                Q(is_organization_private=True, is_private=False, organizations__in=user.profile.organizations.all()) |
                Q(is_organization_private=True, is_private=True, organizations__in=user.profile.organizations.all(),
                  private_courseants=user.profile)
            )


            q |= Q(organizers=user.profile)
            queryset = queryset.filter(q)
        return queryset.distinct()

    def rate(self):
        print('rating course')
        # Rating.objects.filter(course__end_time__gte=self.end_time).delete()
        # for course in course.objects.filter(is_rated=True, end_time__gte=self.end_time).order_by('end_time'):
        #     rate_course(course)

    class Meta:
        permissions = (
            ('see_private_course', _('See private courses')),
            ('edit_own_course', _('Edit own courses')),
            ('edit_all_course', _('Edit all courses')),
            ('clone_course', _('Clone course')),
            ('moss_course', _('MOSS course')),
            ('course_rating', _('Rate courses')),
            ('course_access_code', _('course access codes')),
            ('create_private_course', _('Create private courses')),
            ('change_course_visibility', _('Change course visibility')),
            ('course_problem_label', _('Edit course problem label script')),
            ('lock_course', _('Change lock status of course')),
        )
        verbose_name = _('course')
        verbose_name_plural = _('courses')


class Topic(models.Model):
    key = models.CharField(max_length=20, verbose_name=_('topic id'),
                validators=[RegexValidator('^[a-z0-9]+$', _('topic id must be ^[a-z0-9]+$'))])
    name = models.CharField(max_length=100, verbose_name=_('Topic name'))
    course = models.ForeignKey(Course, on_delete=models.CASCADE, db_index=True)
    order = models.PositiveIntegerField(default=1)
    is_visible = models.BooleanField(default=True)

    class Meta:
        unique_together = ('course', 'key')
    
    def is_visible_for(self, user):
        return self.course.is_visible_for(user)
    
    def __str__(self) -> str:
        return self.name


class SubTopic(models.Model):
    key = models.CharField(max_length=20, verbose_name=_('sub topic id'),
                validators=[RegexValidator('^[a-z0-9]+$', _('sub topic id must be ^[a-z0-9]+$'))])
    name = models.CharField(max_length=100, verbose_name=_('SubTopic name'))
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, db_index=True)
    order = models.PositiveIntegerField(default=1)
    is_visible = models.BooleanField(default=True)

    class Meta:
        unique_together = ('topic', 'key')

    def __str__(self) -> str:
        return self.name


class CourseParticipation(models.Model):
    LIVE = 0
    SPECTATE = -1

    course = models.ForeignKey(Course, verbose_name=_('associated course'), related_name='users', on_delete=CASCADE)
    user = models.ForeignKey(Profile, verbose_name=_('user'), related_name='course_history', on_delete=CASCADE)
    real_start = models.DateTimeField(verbose_name=_('start time'), default=timezone.now, db_column='start')
    score = models.FloatField(verbose_name=_('score'), default=0, db_index=True)
    cumtime = models.PositiveIntegerField(verbose_name=_('cumulative time'), default=0)
    is_disqualified = models.BooleanField(verbose_name=_('is disqualified'), default=False,
                                          help_text=_('Whether this participation is disqualified.'))
    tiebreaker = models.DateTimeField(verbose_name=_('tie-breaking field'), null=True, blank=True)
    format_data = JSONField(verbose_name=_('course format specific data'), null=True, blank=True)

    def recompute_results(self):
        with transaction.atomic():
            self.course.format.update_participation(self)
            if self.is_disqualified:
                self.score = -9999
                self.save(update_fields=['score'])
    recompute_results.alters_data = True

    def set_disqualified(self, disqualified):
        self.is_disqualified = disqualified
        self.recompute_results()
        # if self.course.is_rated and self.course.ratings.exists():
        #     self.course.rate()
        if self.is_disqualified:
            # if self.user.current_course == self:
            #     self.user.remove_course()
            self.course.banned_users.add(self.user)
        else:
            self.course.banned_users.remove(self.user)
    set_disqualified.alters_data = True

    # @property
    # def live(self):
    #     return self.virtual == self.LIVE

    # @property
    # def spectate(self):
    #     return self.virtual == self.SPECTATE

    # @cached_property
    # def start(self):
    #     course = self.course
    #     return course.start_time if course.time_limit is None and (self.live or self.spectate) else self.real_start

    # @cached_property
    # def end_time(self):
    #     course = self.course
    #     if self.spectate:
    #         return course.end_time
    #     if self.virtual:
    #         if course.time_limit:
    #             return self.real_start + course.time_limit
    #         else:
    #             return self.real_start + (course.end_time - course.start_time)
    #     return course.end_time if course.time_limit is None else \
    #         min(self.real_start + course.time_limit, course.end_time)

    @cached_property
    def _now(self):
        # This ensures that all methods talk about the same now.
        return timezone.now()

    # @property
    # def ended(self):
    #     return self.end_time is not None and self.end_time < self._now

    # @property
    # def time_remaining(self):
    #     end = self.end_time
    #     if end is not None and end >= self._now:
    #         return end - self._now

    def __str__(self) -> str:
        return self.user.user.username

    # def __str__(self):
    #     if self.spectate:
    #         return gettext('%s spectating in %s') % (self.user.username, self.course.name)
    #     if self.virtual:
    #         return gettext('%s in %s, v%d') % (self.user.username, self.course.name, self.virtual)
    #     return gettext('%s in %s') % (self.user.username, self.course.name)

    class Meta:
        verbose_name = _('course participation')
        verbose_name_plural = _('course participations')

        unique_together = ('course', 'user')


class CourseProblem(models.Model):
    problem = models.ForeignKey(Problem, verbose_name=_('problem'), related_name='courses', on_delete=CASCADE)
    course = models.ForeignKey(Course, verbose_name=_('course'), related_name='course_problems', on_delete=CASCADE)
    points = models.IntegerField(verbose_name=_('points'))
    partial = models.BooleanField(default=True, verbose_name=_('partial'))
    is_pretested = models.BooleanField(default=False, verbose_name=_('is pretested'))
    is_visible = models.BooleanField(default=True)
    subtopic = models.ForeignKey(SubTopic, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(verbose_name=_('order'))
    output_prefix_override = models.IntegerField(verbose_name=_('output prefix length override'),
                                                 default=0, null=True, blank=True)

    class Meta:
        unique_together = ('problem', 'course')
        index_together = ('subtopic', 'order')
        verbose_name = _('course problem')
        verbose_name_plural = _('course problems')
    
    def save(self, *args, **kwargs):
        super(CourseProblem, self).save(*args, **kwargs)
        self.problem.is_public = self.is_visible
        self.problem.save()
        
    def clean(self):
        self.course = self.subtopic.topic.course


class CourseSubmission(models.Model):
    submission = models.OneToOneField(Submission, verbose_name=_('submission'),
                                      related_name='course', on_delete=CASCADE)
    problem = models.ForeignKey(CourseProblem, verbose_name=_('problem'), on_delete=CASCADE,
                                related_name='submissions', related_query_name='submission')
    participation = models.ForeignKey(CourseParticipation, verbose_name=_('participation'), on_delete=CASCADE,
                                      related_name='submissions', related_query_name='submission')
    points = models.FloatField(default=0.0, verbose_name=_('points'))
    is_pretest = models.BooleanField(verbose_name=_('is pretested'),
                                     help_text=_('Whether this submission was ran only on pretests.'),
                                     default=False)

    class Meta:
        verbose_name = _('course submission')
        verbose_name_plural = _('course submissions')
    
    def update_score(self):
        ps = CourseSubmission.objects.exclude(id=self.id).filter(participation=self.participation, problem=self.problem).order_by('-submission__points').first()
        self.points = (self.submission.points*self.problem.points)/self.problem.problem.points
        self.save()
        if ps:
            if ps.points<self.points:
                self.participation.score -= ps.points
                self.participation.score += self.points
                self.participation.tiebreaker = self.submission.date
                self.participation.save()
        else:
            self.participation.score += self.points
            self.participation.tiebreaker = self.submission.date
            self.participation.save()


# class Rating(models.Model):
#     user = models.ForeignKey(Profile, verbose_name=_('user'), related_name='ratings', on_delete=CASCADE)
#     course = models.ForeignKey(Course, verbose_name=_('course'), related_name='ratings', on_delete=CASCADE)
#     participation = models.OneToOneField(CourseParticipation, verbose_name=_('participation'),
#                                          related_name='rating', on_delete=CASCADE)
#     rank = models.IntegerField(verbose_name=_('rank'))
#     rating = models.IntegerField(verbose_name=_('rating'))
#     volatility = models.IntegerField(verbose_name=_('volatility'))
#     last_rated = models.DateTimeField(db_index=True, verbose_name=_('last rated'))

#     class Meta:
#         unique_together = ('user', 'course')
#         verbose_name = _('course rating')
#         verbose_name_plural = _('course ratings')


# class courseMoss(models.Model):
#     LANG_MAPPING = [
#         ('C', MOSS_LANG_C),
#         ('C++', MOSS_LANG_CC),
#         ('Java', MOSS_LANG_JAVA),
#         ('Python', MOSS_LANG_PYTHON),
#     ]

#     course = models.ForeignKey(course, verbose_name=_('course'), related_name='moss', on_delete=CASCADE)
#     problem = models.ForeignKey(Problem, verbose_name=_('problem'), related_name='moss', on_delete=CASCADE)
#     language = models.CharField(max_length=10)
#     submission_count = models.PositiveIntegerField(default=0)
#     url = models.URLField(null=True, blank=True)

#     class Meta:
#         unique_together = ('course', 'problem', 'language')
#         verbose_name = _('course moss result')
#         verbose_name_plural = _('course moss results')



## problem, profile to courses = pr.course_set.filter(users__user=p)