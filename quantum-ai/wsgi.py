"""WSGI entrypoint for production servers.

Exposes the Flask `app` from fraud_detection_api for Gunicorn/uWSGI.
Usage examples:
  gunicorn -w 2 -b 0.0.0.0:5050 wsgi:app
"""
from fraud_detection_api import app
