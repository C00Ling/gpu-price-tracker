web: uvicorn main:app --host 0.0.0.0 --port $PORT
worker: celery -A jobs.celery_app worker --loglevel=info
beat: celery -A jobs.celery_app beat --loglevel=info
