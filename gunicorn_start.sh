#!/bin/bash
# Name of the application
NAME="site"
# Django project directory
DJANGODIR=/media/k/media/workspace/onlineJudge/server/site
# we will communicte using this unix socket
SOCKFILE=/home/k/tmp/dmoj-site.sock
# the user to run as
#USER=ubuntu
# the group to run as
#GROUP=ubuntu
# how many worker processes should Gunicorn spawn
NUM_WORKERS=3
# which settings file should Django use
DJANGO_SETTINGS_MODULE=dmoj.settings
# WSGI module name
DJANGO_WSGI_MODULE=dmoj.wsgi
#echo "Starting $NAME as `whoami`"
# Activate the virtual environment
cd $DJANGODIR
source /media/k/media/workspace/onlineJudge/server/dmojsite/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH
# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR
# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
# --name $NAME \
# --user=$USER --group=$GROUP \
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
--workers $NUM_WORKERS \
--bind=unix:$SOCKFILE \
--log-level=debug \
--log-file=-
