#!/usr/bin/env bash
# Render build script (Render runs it with: bash build.sh)
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py seed_site

# Create the staff login, or reset its password, from the
# DJANGO_SUPERUSER_USERNAME / _EMAIL / _PASSWORD environment variables.
python manage.py ensure_admin
