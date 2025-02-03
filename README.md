# Blog API

A FastAPI and Django-based Blog API that provides endpoints for managing blog posts.

## Features

- CRUD operations for blog posts
- Image upload support
- Automatic slug generation
- CORS enabled
- Asynchronous request handling

## Requirements

- Python 3.13+
- Virtual environment

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Abudi-seid10/Blogapi.git
cd blog-api
```

2. Create and activate virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Django:
```bash
cd blog_backend
python manage.py migrate
python manage.py createsuperuser
```

## Running the Application

1. Start the FastAPI server:
```bash
cd blog_backend/fastapi_app
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

2. Access the API at: http://localhost:8000
3. API Documentation at: http://localhost:8000/docs

## API Endpoints

### Posts

- `GET /posts` - List all posts
- `GET /posts/{slug}` - Get a specific post
- `POST /posts` - Create a new post
  ```json
  {
    "title": "Post Title",
    "content": "Post Content",
    "image": "optional-image-url"
  }
  ```

### Health Check

- `GET /health` - Check API health status

## Development

- The application uses FastAPI for the API layer and Django for the database and admin interface
- CORS is enabled for development with all origins allowed
- Images are stored in the `media/post_images` directory
- Logs are available in the console with DEBUG level enabled

## Production Deployment

1. Update CORS settings in `main.py` to restrict allowed origins
2. Set DEBUG=False in Django settings
3. Configure proper database settings
4. Use Gunicorn with Uvicorn workers:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
