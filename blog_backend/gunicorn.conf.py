bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
wsgi_app = "fastapi_app.main:app"
pythonpath = "/home/ubuntu/Blogapi/blog_backend"
accesslog = "-"
errorlog = "-"
