from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from course.models import Course, Topic, SubTopic, CourseProblem
from judge.models import Problem

courses = [
    {
        'key': 'beginnersCP',
        'name': 'Beginner CP',
        'description':'''
            Beginner means someone who has just gone through an introductory Python course. He can solve some problems with 1 or 2 Python classes or functions. Normally, the answers could directly be found in the textbooks.
        ''',
        'is_visible': True,
        'topics': [
            {
                'key': 'basics',
                'name': 'Basics',
                'order':1,
                'is_visible':True,
                'sub-topics':[
                    {
                        'key': 'io',
                        'name': 'Input Output',
                        'order':1,
                        'is_visible':False,
                        'problems':[
                            {
                                'problem':'aplusb',
                                'points':10
                            }
                        ]
                    },
                    {
                        'key': 'loop',
                        'name': 'Loops',
                        'order':2,
                        'is_visible':False
                    },
                    {
                        'key': 'arraysstrings',
                        'name': 'Arrays and String',
                        'order':3,
                        'is_visible':False,   
                    }
                ]
            },
            
            {
                'key': 'recursion',
                'name': 'Recursion and Backtracking',
                'order':4,
                'is_visible':True,
                'sub-topics':[
                    {
                        'key': 'basic',
                        'name': 'Basics',
                        'order':1,
                        'is_visible':False,
                    },
                    {
                        'key': 'memo',
                        'name': 'Memoization',
                        'order':2,
                        'is_visible':False
                    },
                    {
                        'key': 'dp',
                        'name': 'Dynamic Programming',
                        'order':3,
                        'is_visible':False,   
                    }
                ]
            },
            {
                'key': 'basicds',
                'name': 'Basic Data Structures',
                'order':5,
                'is_visible':True,
                'sub-topics':[
                    {
                        'key': 'stackqueue',
                        'name': 'Stack and Queue',
                        'order':1,
                        'is_visible':False,
                    },
                    {
                        'key': 'linkedlist',
                        'name': 'Linked List',
                        'order':2,
                        'is_visible':False
                    },
                    {
                        'key': 'tree',
                        'name': 'Tree',
                        'order':3,
                        'is_visible':False,   
                    }
                ]
            },
            {
                'key': 'advancedds',
                'name': 'Advanced Data Structure',
                'order':6,
                'is_visible':True,
                'sub-topics':[
                    {
                        'key': 'hashmapheap',
                        'name': 'HashMap and Heap',
                        'order':1,
                        'is_visible':False,
                    },
                    {
                        'key': 'graph',
                        'name': 'Graph',
                        'order':3,
                        'is_visible':False,   
                    }
                ]
            }
        ]
    },
    {
        'key': 'intermediateCP',
        'name': 'Intermediate CP',
        'description':'''
            Intermediate means someone who has just learned Python, but already has a relatively strong programming background from before. He should be able to solve problems which may involve 3 or 3 Python classes or functions. The answers cannot be directly be found in the textbooks.
        ''',
        'is_visible': True
    },
    {
        'key': 'advancedCP',
        'name': 'Advanced CP',
        'description':'''
            He should use Python to solve more complex problem using more rich libraries functions and data structures and algorithms. He is supposed to solve the problem using several Python standard packages and advanced techniques.
        ''',
        'is_visible': True
    }
]
class Command(BaseCommand):
    help = 'creates sample course'

    def add_arguments(self, parser):
        print('add args')
        return
        parser.add_argument('name', help='username')
        parser.add_argument('email', help='email, not necessary to be resolvable')
        parser.add_argument('password', help='password for the user')
        parser.add_argument('language', nargs='?', default=settings.DEFAULT_USER_LANGUAGE,
                            help='default language ID for user')

        parser.add_argument('--superuser', action='store_true', default=False,
                            help="if specified, creates user with superuser privileges")
        parser.add_argument('--staff', action='store_true', default=False,
                            help="if specified, creates user with staff privileges")

    def handle(self, *args, **options):
        print('handle')
        
        for c in courses:
            course, created = Course.objects.get_or_create(key=c['key'])
            if created:
                course.name = c['name']
                course.description = c['description']
                course.is_visible = c['is_visible'] if 'is_visible' in c else False
                course.save()
            if 'topics' not in c:
                continue
            for ti, t in enumerate(c['topics']):
                topic, created = Topic.objects.get_or_create(key=t['key'], course=course)
                if created:
                    topic.name = t['name']
                    topic.is_visible = t['is_visible'] if 'is_visible' in t else False
                topic.order = ti
                topic.save()
                if 'sub-topics' not in t:
                    continue
                for sti, st in enumerate(t['sub-topics']):
                    subtopic, created = SubTopic.objects.get_or_create(key=st['key'], topic=topic)
                    if created:
                        subtopic.name = st['name']
                        subtopic.is_visible = st['is_visible'] if 'is_visible' in st else False
                    subtopic.order = sti
                    subtopic.save()
                    if 'problems' not in st:
                        continue
                    for pi, p in enumerate(st['problems']):
                        problem = Problem.objects.get(code=p['problem'])
                        cp = CourseProblem(problem=problem, course=course,subtopic=subtopic)
                        if 'points' in p:
                            cp.points = p['points']
                        if 'order' in p:
                            cp.order = p['order']
                        else :
                            cp.order = pi
                        cp.save()

                    
