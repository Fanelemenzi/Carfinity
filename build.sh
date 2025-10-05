#!/usr/bin/env bash
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Create the staticfiles_build directory for Vercel
mkdir -p staticfiles_build
cp -r staticfiles/* staticfiles_build/

# Ensure templates directory is accessible
echo "Templates directory contents:"
ls -la templates/
echo "Public templates:"
ls -la templates/public/

#python manage.py migrate