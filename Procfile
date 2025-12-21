web: ./start.sh
worker: celery -A jobs.celery_app worker --loglevel=info
beat: celery -A jobs.celery_app beat --loglevel=info
