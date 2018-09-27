#!/usr/bin/env bash
gunicorn -w 3 -b 0.0.0.0:8010 exchange.wsgi
