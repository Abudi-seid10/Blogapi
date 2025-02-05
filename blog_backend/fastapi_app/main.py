import os
import sys
import logging

# Add Django project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_backend.settings')
import django
django.setup()

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Union
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from django.contrib.auth.models import User
from blog.models import Post, Category, Tag, UserProfile, Comment, Reaction, Bookmark
from django.db.models import Q, Count
import feedgenerator
from asgiref.sync import sync_to_async

# JWT settings
SECRET_KEY = "c4debad33d82a88d5ec488d21b5dfbc6ec45110d6405735c43125a1763d0fca8af5bbeb92d575591b27a952e5a683ce5a1501c011ab59b2ed750b7b74dbd87924b524a0b393ed90a127eeff8c350301ae8ceb2ec77e7e961ddf0ed254119a271f9009bc3d7563a7db915016e29debb7fb8b5cefd78599a2ea77bae39e97b8139fae9b18710a2d2aa5cdc3785e4263d9359f9f5fb93c4f73e7f7fd4869a2b0a29becf038979cb3e04c302e41dd6102bfa9fb11b1546f464f534a0a8608e54a026f49c69acc7831077f242cf5686d5dad081aea1316c56e4d05ef2188d4bb0da8de93d59b09964706cbcfaa03f02a6f7712446a4b75f8efaa1667cdd85c87ed800"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set recursion limit
sys.setrecursionlimit(3000)

# ---------- Django Setup ----------
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

class PostResponse(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    created_at: datetime
    updated_at: datetime
    is_draft: bool
    view_count: int = 0
    likes: int = 0
    dislikes: int = 0
    image: Optional[str] = None
    author_username: Optional[str] = None
    category_name: Optional[str] = None
    tags: List[str] = []
    estimated_read_time: int = 0

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    bio: Optional[str] = None
    website: Optional[str] = None

class CategoryBase(BaseModel):
    name: str
    slug: str

class TagBase(BaseModel):
    name: str
    slug: str

class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[int] = None

class CommentResponse(BaseModel):
    id: int
    content: str
    author_username: str
    created_at: datetime
    replies: List['CommentResponse'] = []

    class Config:
        from_attributes = True

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)
    except jwt.JWTError:
        raise HTTPException(status_code=401)
    user = User.objects.filter(username=username).first()
    if user is None:
        raise HTTPException(status_code=401)
    return user

# ---------- Serialization ----------
async def serialize_post(post_dict: dict) -> dict:
    # Convert QueryDict to regular dict if needed
    if hasattr(post_dict, '__dict__'):
        post_dict = post_dict.__dict__

    # Remove Django's internal state field
    post_dict.pop('_state', None)
    
    # Handle image field
    image = post_dict.get('image', None)
    post_dict['image'] = str(image.url) if image and hasattr(image, 'url') else None
    
    # Handle author username
    author_id = post_dict.get('author_id', None)
    if author_id:
        try:
            author = await sync_to_async(User.objects.get)(id=author_id)
            post_dict['author_username'] = author.username
        except User.DoesNotExist:
            post_dict['author_username'] = None
    else:
        post_dict['author_username'] = None

    # Handle category name
    category_id = post_dict.get('category_id', None)
    if category_id:
        try:
            category = await sync_to_async(Category.objects.get)(id=category_id)
            post_dict['category_name'] = category.name
        except Category.DoesNotExist:
            post_dict['category_name'] = None
    else:
        post_dict['category_name'] = None

    # Handle tags
    post_dict['tags'] = []
    if 'id' in post_dict:
        try:
            post_tags = await sync_to_async(list)(Tag.objects.filter(post__id=post_dict['id']).values_list('name', flat=True))
            post_dict['tags'] = list(post_tags)
        except Exception:
            pass

    # Ensure all required fields are present with default values
    post_dict.setdefault('view_count', 0)
    post_dict.setdefault('likes', 0)
    post_dict.setdefault('dislikes', 0)
    post_dict.setdefault('estimated_read_time', 0)
    post_dict.setdefault('is_draft', False)
    
    # Convert datetime objects to strings if needed
    for field in ['created_at', 'updated_at']:
        if isinstance(post_dict.get(field), datetime):
            post_dict[field] = post_dict[field].isoformat()

    return post_dict

def serialize_comment(comment):
    return {
        "id": comment.get("id"),
        "content": comment.get("content"),
        "author_username": comment.get("author__username"),
        "created_at": comment.get("created_at"),
        "replies": [serialize_comment(reply) for reply in comment.get("replies", [])]
    }

# ---------- API Endpoints ----------
@app.get("/posts", response_model=List[PostResponse])
async def get_posts(skip: int = Query(default=0, ge=0), limit: int = Query(default=15, le=100)):
    posts = await sync_to_async(list)(Post.objects.all().order_by('-created_at')[skip:skip + limit].values())
    serialized_posts = []
    for post in posts:
        serialized_post = await serialize_post(post)
        serialized_posts.append(serialized_post)
    return serialized_posts

@app.get("/posts/{slug}", response_model=PostResponse)
async def get_post(slug: str):
    try:
        post = await sync_to_async(Post.objects.get)(slug=slug)
        post_dict = await sync_to_async(lambda: post.__dict__)()
        return await serialize_post(post_dict)
    except Post.DoesNotExist:
        raise HTTPException(status_code=404, detail="Post not found")
    except Exception as e:
        logger.error(f"Error fetching post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/posts/trending", response_model=List[PostResponse])
async def get_trending_posts(timeframe: str = Query(default="24h", regex="^(24h|7d|30d)$")):
    time_delta = {
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30)
    }[timeframe]
    
    since = datetime.now() - time_delta
    posts = await sync_to_async(list)(
        Post.objects.filter(created_at__gte=since)
        .order_by('-view_count', '-likes', '-created_at')[:10]
        .values()
    )
    serialized_posts = []
    for post in posts:
        serialized_post = await serialize_post(post)
        serialized_posts.append(serialized_post)
    return serialized_posts

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
        serialized = await serialize_post(db_post.__dict__)
        logger.debug(f"Created post: {serialized}")
        return serialized
    except Exception as e:
        logger.error(f"Error in create_post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/posts/{post_id}/view")
async def increment_view(post_id: int):
    post = await sync_to_async(Post.objects.get)(id=post_id)
    post.view_count += 1
    await sync_to_async(post.save)()
    return {"status": "success"}

@app.post("/posts/{post_id}/like")
async def like_post(post_id: int):
    post = await sync_to_async(Post.objects.get)(id=post_id)
    post.likes += 1
    await sync_to_async(post.save)()
    return {"status": "success"}

@app.post("/users", response_model=dict)
async def create_user(user: UserCreate):
    if await sync_to_async(User.objects.filter(username=user.username).exists)():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    db_user = User(username=user.username, email=user.email)
    db_user.set_password(user.password)  # This properly hashes the password
    await sync_to_async(db_user.save)()
    
    # Create user profile
    profile = UserProfile(user=db_user)
    await sync_to_async(profile.save)()
    
    return {"message": "User created successfully"}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await sync_to_async(User.objects.filter(username=form_data.username).first)()
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=dict)
async def read_users_me(current_user: User = Depends(get_current_user)):
    profile = await sync_to_async(UserProfile.objects.get)(user=current_user)
    return {
        "username": current_user.username,
        "email": current_user.email,
        "bio": profile.bio,
        "website": profile.website
    }

@app.put("/users/me/profile")
async def update_profile(profile: UserProfile, current_user: User = Depends(get_current_user)):
    user_profile = await sync_to_async(UserProfile.objects.get)(user=current_user)
    user_profile.bio = profile.bio
    user_profile.website = profile.website
    await sync_to_async(user_profile.save)()
    return {"message": "Profile updated successfully"}

@app.post("/categories")
async def create_category(category: CategoryBase, current_user: User = Depends(get_current_user)):
    db_category = Category(name=category.name, slug=category.slug)
    await sync_to_async(db_category.save)()
    return {"message": "Category created successfully"}

@app.post("/tags")
async def create_tag(tag: TagBase, current_user: User = Depends(get_current_user)):
    db_tag = Tag(name=tag.name, slug=tag.slug)
    await sync_to_async(db_tag.save)()
    return {"message": "Tag created successfully"}

@app.get("/posts/search")
async def search_posts(q: str = Query(..., min_length=3)):
    posts = await sync_to_async(list)(
        Post.objects.filter(
            Q(title__icontains=q) | Q(content__icontains=q),
            is_draft=False
        ).values()
    )
    serialized_posts = []
    for post in posts:
        serialized_post = await serialize_post(post)
        serialized_posts.append(serialized_post)
    return serialized_posts

@app.post("/posts/{post_id}/comments")
async def create_comment(
    post_id: int,
    comment: CommentCreate,
    current_user: User = Depends(get_current_user)
):
    post = await sync_to_async(Post.objects.get)(id=post_id)
    db_comment = Comment(
        post=post,
        author=current_user,
        content=comment.content,
        parent_id=comment.parent_id
    )
    await sync_to_async(db_comment.save)()
    return {"message": "Comment created successfully"}

@app.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def get_comments(post_id: int):
    comments = await sync_to_async(list)(
        Comment.objects.filter(post_id=post_id, parent=None)
        .select_related('author')
        .prefetch_related('replies')
        .order_by('-created_at')
        .values()
    )
    return [serialize_comment(comment) for comment in comments]

@app.post("/posts/{post_id}/reactions")
async def create_reaction(
    post_id: int,
    reaction_type: str = Query(..., regex="^(like|dislike)$"),
    current_user: User = Depends(get_current_user)
):
    post = await sync_to_async(Post.objects.get)(id=post_id)
    reaction, created = await sync_to_async(Reaction.objects.get_or_create)(
        post=post,
        user=current_user,
        defaults={"reaction_type": reaction_type}
    )
    
    if not created:
        reaction.reaction_type = reaction_type
        await sync_to_async(reaction.save)()
    
    return {"message": "Reaction recorded successfully"}

@app.post("/posts/{post_id}/bookmark")
async def bookmark_post(post_id: int, current_user: User = Depends(get_current_user)):
    post = await sync_to_async(Post.objects.get)(id=post_id)
    _, created = await sync_to_async(Bookmark.objects.get_or_create)(
        post=post,
        user=current_user
    )
    return {"message": "Post bookmarked successfully"}

@app.get("/users/me/bookmarks")
async def get_bookmarks(current_user: User = Depends(get_current_user)):
    bookmarks = await sync_to_async(list)(
        Bookmark.objects.filter(user=current_user)
        .select_related('post')
        .order_by('-created_at')
        .values('post')
    )
    return [await serialize_post(bookmark['post']) for bookmark in bookmarks]

@app.get("/posts/{post_id}/related")
async def get_related_posts(post_id: int):
    post = await sync_to_async(Post.objects.get)(id=post_id)
    related_posts = await sync_to_async(list)(
        Post.objects.filter(
            Q(category=post.category) | Q(tags__in=post.tags.all())
        )
        .exclude(id=post_id)
        .distinct()
        .order_by('-created_at')[:5]
        .values()
    )
    serialized_posts = []
    for post in related_posts:
        serialized_post = await serialize_post(post)
        serialized_posts.append(serialized_post)
    return serialized_posts

@app.get("/feed/rss")
async def get_rss_feed():
    feed = feedgenerator.Rss201rev2Feed(
        title="Blog API Feed",
        link="http://example.com",
        description="Latest blog posts",
        language="en"
    )
    
    posts = await sync_to_async(
        Post.objects.filter(is_draft=False)
        .order_by('-created_at')[:10]
        .values()
    )()
    
    for post in posts:
        feed.add_item(
            title=post.title,
            link=f"http://example.com/posts/{post.slug}",
            description=post.content[:200],
            pubdate=post.created_at
        )
    
    return Response(
        content=feed.writeString('utf-8'),
        media_type="application/xml"
    )

@app.post("/posts/{post_id}/share")
async def share_post(post_id: int):
    post = await sync_to_async(Post.objects.get)(id=post_id)
    share_url = f"http://example.com/posts/{post.slug}"
    return {
        "share_urls": {
            "twitter": f"https://twitter.com/intent/tweet?url={share_url}",
            "facebook": f"https://www.facebook.com/sharer/sharer.php?u={share_url}",
            "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={share_url}"
        }
    }

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
        content={"detail": str(exc)}
    )

# ---------- Health Check ----------
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0"}