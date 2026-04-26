# Gunicorn configuration for Render deployment
# Increase timeout to handle long Excel/PDF exports

workers    = 1          # 1 worker on free tier (512MB RAM)
timeout    = 300        # 5 minutes (default is 30s — too short for exports)
keepalive  = 5
bind       = "0.0.0.0:10000"
worker_class = "sync"

# Logging
accesslog  = "-"
errorlog   = "-"
loglevel   = "info"
