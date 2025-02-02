# Blog API

A modern blog API built with Django and FastAPI, providing a robust backend for blog management.

## Technologies Used

- Django (Backend ORM and Admin)
- FastAPI (API Layer)
- SQLite (Database)
- Uvicorn (ASGI Server)

## Project Structure

```
blog_backend/
├── blog/                  # Django app for blog models
│   ├── models.py         # Blog data models
│   └── admin.py          # Django admin configuration
├── fastapi_app/          # FastAPI application
│   └── main.py          # API endpoints and business logic
└── blog_backend/         # Django project settings
    └── settings.py       # Project configuration
```

## Features

- RESTful API endpoints for blog posts
- Django Admin interface for content management
- Async API operations with Django ORM
- Image upload support for posts
- User authentication and authorization
- CORS support for frontend integration

## API Endpoints

- `GET /posts` - List all blog posts
- `GET /posts/{slug}` - Get a specific post by slug
- `POST /posts` - Create a new blog post

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install django fastapi uvicorn asgiref
```

3. Run migrations:
```bash
cd blog_backend
python manage.py migrate
```

4. Create a superuser:
```bash
python manage.py createsuperuser
```

5. Run the FastAPI server:
```bash
cd fastapi_app
python -m uvicorn main:app --reload
```

6. Access the API at `http://127.0.0.1:8000`
7. Access the Django admin at `http://127.0.0.1:8001/admin`

## Deployment Instructions

The application is configured for Heroku deployment:

1. Install Heroku CLI
2. Login to Heroku: `heroku login`
3. Create app: `heroku create your-app-name`
4. Set environment variables in Heroku dashboard
5. Deploy: `git push heroku main`

## API Request Examples

### Create a Post
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/posts' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Sample Post",
    "content": "This is a sample post content",
    "slug": "sample-post"
  }'
```

### Get All Posts
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/posts' \
  -H 'accept: application/json'
```

## Development Notes

- Set `DEBUG = True` in settings.py for development
- Configure `ALLOWED_HOSTS` in production
- Use environment variables for sensitive data
- Configure CORS settings based on your frontend URL
