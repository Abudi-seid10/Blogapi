import os
import sys
import logging
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from asgiref.sync import sync_to_async

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set recursion limit
sys.setrecursionlimit(3000)

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
logger.debug(f"Added {project_root} to Python path")

# ---------- Django Setup ----------
# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_backend.settings')
import django
django.setup()

# Import Django models after setup
from blog.models import Post
from django.contrib.auth.models import User

# Get User model
User = User

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

# ---------- Pydantic Schemas ----------
class PostBase(BaseModel):
    title: str
    content: str
    image: Optional[str] = None
    
    class Config:
        from_attributes = True

class PostCreate(PostBase):
    pass

class PostResponse(PostBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author_id: Optional[int] = None
    slug: str

    class Config:
        from_attributes = True

# ---------- Serialization ----------
def serialize_post(post):
    try:
        data = {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "image": str(post.image.url) if post.image else None,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "updated_at": post.updated_at.isoformat() if post.updated_at else None,
            "author_id": post.author_id if hasattr(post, 'author_id') else None,
            "slug": post.slug
        }
        logger.debug(f"Serialized post: {data}")
        return data
    except Exception as e:
        logger.error(f"Error serializing post: {e}")
        raise

# ---------- API Endpoints ----------
@app.get("/posts", response_model=List[PostResponse])
async def get_posts():
    try:
        logger.debug("Fetching all posts")
        posts = await sync_to_async(list)(Post.objects.all())
        logger.debug(f"Found {len(posts)} posts")
        serialized = [serialize_post(post) for post in posts]
        logger.debug(f"Serialized posts: {serialized}")
        return serialized
    except Exception as e:
        logger.error(f"Error in get_posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/posts/{slug}", response_model=PostResponse)
async def get_post(slug: str):
    try:
        logger.debug(f"Fetching post with slug: {slug}")
        post = await sync_to_async(Post.objects.get)(slug=slug)
        serialized = serialize_post(post)
        logger.debug(f"Serialized post: {serialized}")
        return serialized
    except Post.DoesNotExist:
        logger.error(f"Post not found with slug: {slug}")
        raise HTTPException(status_code=404, detail="Post not found")
    except Exception as e:
        logger.error(f"Error in get_post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/posts", response_model=PostResponse)
async def create_post(post: PostCreate):
    try:
        logger.debug("Creating new post")
        default_user = await sync_to_async(User.objects.first)()
        if not default_user:
            logger.debug("Creating default user")
            default_user = await sync_to_async(User.objects.create)(
                username="default_user",
                email="default@example.com"
            )
        
        db_post = Post(
            title=post.title,
            content=post.content,
            image=post.image,
            author=default_user,
            slug=post.title.lower().replace(" ", "-")
        )
        logger.debug(f"Saving post: {db_post.__dict__}")
        await sync_to_async(db_post.save)()
        serialized = serialize_post(db_post)
        logger.debug(f"Created post: {serialized}")
        return serialized
    except Exception as e:
        logger.error(f"Error in create_post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ---------- Startup Event ----------
@app.on_event("startup")
async def startup_event():
    try:
        user_exists = await sync_to_async(User.objects.filter(username="default_user").exists)()
        if not user_exists:
            user = User(username="default_user", email="default@example.com")
            await sync_to_async(user.set_password)("defaultpassword123")
            await sync_to_async(user.save)()
    except Exception as e:
        print(f"Error creating default user: {e}")

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

# ---------- Health Check ----------
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0"}