#!/usr/bin/env bash
# Terminar el script si hay algún error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate