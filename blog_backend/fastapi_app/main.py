# fastapi_app/main.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from asgiref.sync import sync_to_async
import asyncio

# ---------- Django Setup ----------
# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blog_backend.settings")
import django
django.setup()

# Import Django models after setup
from blog.models import Post
from django.contrib.auth import get_user_model

# Get User model
User = get_user_model()

# ---------- FastAPI Setup ----------
app = FastAPI(title="Blog API", version="1.0")

# Add CORS middleware with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Startup Event ----------
@app.on_event("startup")
async def startup_event():
    get_or_create = sync_to_async(User.objects.get_or_create)
    app.state.default_user, _ = await get_or_create(
        username='default_user',
        defaults={'email': 'default@example.com', 'is_staff': True}
    )

# ---------- Error Handlers ----------
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# ---------- Pydantic Schemas ----------
class PostBase(BaseModel):
    title: str
    content: str
    slug: str
    author_id: int | None = None
    image: str | None = None

    class Config:
        from_attributes = True

class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    id: int
    created_at: datetime
    updated_at: datetime

# ---------- API Endpoints ----------
@app.get("/posts", response_model=List[PostResponse])
async def get_all_posts():
    """Get all blog posts"""
    try:
        get_posts = sync_to_async(lambda: list(Post.objects.all().order_by('-created_at')))
        posts = await get_posts()
        return [jsonable_encoder(post) for post in posts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/posts/{slug}", response_model=PostResponse)
async def get_post_by_slug(slug: str):
    """Get a single post by slug"""
    try:
        get_post = sync_to_async(Post.objects.get)
        post = await get_post(slug=slug)
        return jsonable_encoder(post)
    except Post.DoesNotExist:
        raise HTTPException(status_code=404, detail="Post not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/posts", response_model=PostResponse)
async def create_post(post: PostCreate):
    """Create new blog post (add authentication later)"""
    try:
        exists = sync_to_async(Post.objects.filter(slug=post.slug).exists)
        if await exists():
            raise HTTPException(status_code=400, detail="Slug already exists")
        
        create_post = sync_to_async(Post.objects.create)
        new_post = await create_post(
            title=post.title,
            content=post.content,
            slug=post.slug,
            author_id=post.author_id or app.state.default_user.id,
            image=post.image if post.image else None
        )
        return jsonable_encoder(new_post)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Health Check ----------
@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0"}