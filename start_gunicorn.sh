#!/bin/sh
gunicorn --daemon --pid django.pid -w 3 -b 0.0.0.0:8010 exchange.wsgi
