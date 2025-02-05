# Blog API

A FastAPI and Django-based Blog API that provides endpoints for managing blog posts.

## Features

- CRUD operations for blog posts
- User authentication and profiles
- Categories and tags
- Comments with nested replies
- Post reactions (like/dislike)
- Post bookmarks
- Search functionality
- Trending posts
- Related posts suggestions
- Automatic read time estimation
- View counter
- RSS feed
- Social sharing
- Draft support
- Image upload support
- Pagination
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

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
cd blog_backend
python manage.py migrate
```

4. Start the server:
```bash
uvicorn fastapi_app.main:app --reload
```

## API Endpoints

### Authentication
- `POST /users` - Register new user
  ```json
  {
    "username": "string",
    "email": "user@example.com",
    "password": "string"
  }
  ```
- `POST /token` - Login and get access token
- `GET /users/me` - Get current user profile
- `PUT /users/me/profile` - Update user profile
  ```json
  {
    "bio": "string",
    "website": "string"
  }
  ```

### Posts
- `GET /posts?skip=0&limit=15` - List posts with pagination
- `GET /posts/{slug}` - Get specific post
- `POST /posts` - Create new post
  ```json
  {
    "title": "string",
    "content": "string",
    "image": "optional-image-url"
  }
  ```
- `GET /posts/search?q=query` - Search posts
- `GET /posts/trending?timeframe=24h` - Get trending posts (timeframe: 24h, 7d, 30d)
- `GET /posts/{post_id}/related` - Get related posts
- `POST /posts/{post_id}/view` - Increment post view count
- `POST /posts/{post_id}/share` - Get social sharing links

### Categories & Tags
- `POST /categories` - Create category
  ```json
  {
    "name": "string",
    "slug": "string"
  }
  ```
- `POST /tags` - Create tag
  ```json
  {
    "name": "string",
    "slug": "string"
  }
  ```

### Comments
- `POST /posts/{post_id}/comments` - Add comment
  ```json
  {
    "content": "string",
    "parent_id": "optional-int"
  }
  ```
- `GET /posts/{post_id}/comments` - Get post comments

### Reactions & Bookmarks
- `POST /posts/{post_id}/reactions?reaction_type=like` - React to post (like/dislike)
- `POST /posts/{post_id}/bookmark` - Bookmark post
- `GET /users/me/bookmarks` - Get user's bookmarks

### Feed
- `GET /feed/rss` - Get RSS feed

### Health Check
- `GET /health` - API health check

## Authentication

All endpoints except health check, post listing, and RSS feed require authentication. Include the access token in the Authorization header:

```
Authorization: Bearer your-access-token
```

## Response Format

### Success Response
```json
{
  "id": 1,
  "title": "Post Title",
  "content": "Post content",
  "image": "image_url",
  "created_at": "2024-02-03T19:19:26",
  "updated_at": "2024-02-03T19:19:26",
  "author_username": "user",
  "slug": "post-title",
  "view_count": 0,
  "likes": 0,
  "category": "Technology",
  "tags": ["python", "api"],
  "estimated_read_time": 5,
  "is_draft": false
}
```

### Error Response
```json
{
  "detail": "Error message"
}
```

## Development

- Logs are available in the console with DEBUG level enabled
- Images are stored in the `media/post_images` directory
- Avatars are stored in the `media/avatars` directory

## Production Deployment

1. Update CORS settings in `main.py` to restrict allowed origins
2. Set DEBUG=False in Django settings
3. Configure proper database settings
4. Use Gunicorn with Uvicorn workers:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```
5. Change the SECRET_KEY in production
6. Set up proper media file handling
7. Configure SSL/TLS
8. Set up proper caching
