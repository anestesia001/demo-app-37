import multiprocessing
import os

bind = os.getenv("GUNICORN_BIND", "127.0.0.1:8080")
workers = int(os.getenv("GUNICORN_WORKERS", str(max(2, multiprocessing.cpu_count() * 2 + 1))))
worker_class = "sync"
timeout = 30
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
capture_output = True

graceful_timeout = 20
