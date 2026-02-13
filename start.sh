#!/usr/bin/env bash
set -e

# Move into the project folder
cd Stock-Scanner

# Install Python dependencies
pip install -r requirements.txt

# Start the web server via gunicorn
exec gunicorn app:app --bind 0.0.0.0:${PORT}
