#!/bin/bash
#!/bin/bash
gunicorn --bind 0.0.0.0:$PORT app.main:app --workers 1 --threads 1 --worker-class uvicorn.workers.UvicornWorker --timeout 120
