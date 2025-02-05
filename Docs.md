# Blog API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
The API uses JWT (JSON Web Token) for authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

### Authentication Endpoints

#### Create User
```http
POST /users
Content-Type: application/json

{
    "username": "string",
    "email": "user@example.com",
    "password": "string"
}

Response: {
    "message": "User created successfully"
}
```

#### Login
```http
POST /token
Content-Type: application/x-www-form-urlencoded

username=string&password=string

Response: {
    "access_token": "string",
    "token_type": "bearer"
}
```

## Blog Posts

### Create Post
```http
POST /posts
Authorization: Bearer <token>
Content-Type: application/json

{
    "title": "string",
    "content": "string",
    "image": "string" (optional)
}

Response: PostResponse
```

### Get Posts
```http
GET /posts?skip=0&limit=15

Response: List[PostResponse]
```

### Get Single Post
```http
GET /posts/{slug}

Response: PostResponse
```

### Get Trending Posts
```http
GET /posts/trending?timeframe=24h
timeframe options: 24h, 7d, 30d

Response: List[PostResponse]
```

### Search Posts
```http
GET /posts/search?q=query
Minimum query length: 3 characters

Response: List[PostResponse]
```

### Increment View Count
```http
POST /posts/{post_id}/view
Authorization: Bearer <token>

Response: {
    "message": "View count incremented"
}
```

## Comments

### Create Comment
```http
POST /posts/{post_id}/comments
Authorization: Bearer <token>
Content-Type: application/json

{
    "content": "string",
    "parent_id": integer (optional, for replies)
}

Response: CommentResponse
```

### Get Comments
```http
GET /posts/{post_id}/comments

Response: List[CommentResponse]
```

## Reactions and Interactions

### Create Reaction
```http
POST /posts/{post_id}/reactions?reaction_type=like
Authorization: Bearer <token>
reaction_type options: like, dislike

Response: {
    "message": "Reaction created"
}
```

### Bookmark Post
```http
POST /posts/{post_id}/bookmark
Authorization: Bearer <token>

Response: {
    "message": "Post bookmarked"
}
```

### Get Bookmarks
```http
GET /bookmarks
Authorization: Bearer <token>

Response: List[PostResponse]
```

## Categories and Tags

### Create Category
```http
POST /categories
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "string",
    "slug": "string"
}

Response: {
    "message": "Category created"
}
```

### Create Tag
```http
POST /tags
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "string",
    "slug": "string"
}

Response: {
    "message": "Tag created"
}
```

## User Profile

### Get Current User
```http
GET /users/me
Authorization: Bearer <token>

Response: {
    "username": "string",
    "email": "string"
}
```

### Update Profile
```http
PUT /users/profile
Authorization: Bearer <token>
Content-Type: application/json

{
    "bio": "string",
    "website": "string"
}

Response: {
    "message": "Profile updated"
}
```

## Additional Features

### Get Related Posts
```http
GET /posts/{post_id}/related

Response: List[PostResponse]
```

### Share Post
```http
POST /posts/{post_id}/share

Response: {
    "social_links": {
        "twitter": "string",
        "facebook": "string",
        "linkedin": "string"
    }
}
```

### RSS Feed
```http
GET /feed

Response: RSS 2.0 Feed
```

## Response Models

### PostResponse
```json
{
    "id": "integer",
    "title": "string",
    "slug": "string",
    "content": "string",
    "created_at": "datetime",
    "updated_at": "datetime",
    "is_draft": "boolean",
    "view_count": "integer",
    "likes": "integer",
    "dislikes": "integer",
    "image": "string",
    "author_username": "string",
    "category_name": "string",
    "tags": ["string"],
    "estimated_read_time": "integer"
}
```

### CommentResponse
```json
{
    "id": "integer",
    "content": "string",
    "author_username": "string",
    "created_at": "datetime",
    "replies": ["CommentResponse"]
}
```

## Error Responses
```json
{
    "detail": "Error message"
}
```

Common HTTP Status Codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error
