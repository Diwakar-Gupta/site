from django.core.management.base import BaseCommand
import json 
from os import listdir
from os.path import isfile, join
from judge.models import Problem, Language, ProblemType, ProblemGroup

class Command(BaseCommand):
    help = 'creates problems'

    def add_arguments(self, parser):
        # print(parser)
        parser.add_argument('path', help='path to problems directory /media/.../nativeproblem')

    def handle(self, *args, **options):
        # print(args, options)
        PATH = options.get('path')
        print(PATH)
        languages = Language.objects.all()
        typee = ProblemType.objects.first()
        group = ProblemGroup.objects.first()
        for f in listdir(PATH):
            problemfile = open(join(PATH, f))
            problemjson = json.load(problemfile)
            print(problemjson['code'])
            if Problem.objects.filter(code=problemjson['code']).exists():
                continue
            problem = Problem(code=problemjson['code'])
            print('creating', problem.code)
            problem.name = problemjson['name']
            problem.description = problemjson['description']
            problem.points = problemjson['points']
            problem.is_public = problemjson['is_public'] if 'is_public' in problemjson else True
            problem.memory_limit = problemjson['memory_limit'] if 'memory_limit' in problemjson else 65536
            problem.time_limit = problemjson['time_limit'] if 'time_limit' in problemjson else 10
            problem.group = group
            problem.save()
            for l in languages:
                problem.allowed_languages.add(l)
            problem.types.add(typee)
            problem.save()
            
