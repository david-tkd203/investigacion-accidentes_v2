bind = "0.0.0.0:5005"

vcpus = 4                   
workers = 4
worker_class = "gthread"
threads = 4                 

preload_app = True
timeout = 120
graceful_timeout = 30
keepalive = 2
max_requests = 2000
max_requests_jitter = 200

accesslog = "-"
errorlog = "-"
loglevel = "info"

reload = False
capture_output = True
enable_stdio_inheritance = False
# Opcional: más rápido para tmp
# worker_tmp_dir = "/dev/shm"