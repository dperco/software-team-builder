#!/bin/bash
gunicorn --bind 0.0.0.0:$PORT app.main:app --worker-class uvicorn.workers.UvicornWorker --timeout 120