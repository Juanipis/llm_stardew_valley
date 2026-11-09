# Prompt: Backend Web UI and Authentication

**Your Role:** You are a Python full-stack developer implementing the user-facing web interface for the "StardewEchoes" API.

**Context:** This document details the implementation of the web-based user and API token management system. It covers the authentication flow using JWTs for web sessions, password hashing, and the FastAPI router setup for serving HTML templates and handling user registration and login.

---

## Web-Based User and Token Management

To allow users to register and manage their API token, we will add a simple web interface.

### 1. Web Authentication Flow (JWT)

- A user signs up or logs in via an HTML form.
- Upon successful login, the server generates a JSON Web Token (JWT) and sets it in the user's browser in an `HttpOnly` cookie. This token is used to authenticate subsequent web requests to the dashboard.
- This JWT is separate from the `api_token` used by the Stardew Valley mod.

### 2. Password Hashing and JWT Logic

Add functions to `app/core/security.py` for handling passwords and JWTs.

**`app/core/security.py` (additions):**

```python
import secrets
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- API Token Generation ---
def generate_api_token():
    return secrets.token_hex(32)

# --- JWT for Web Sessions ---
# These should be loaded from your .env file via app.core.config
SECRET_KEY = "your-super-secret-key-for-jwt" # Replace with a real secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### 3. Web UI Routers and Templates

Create a new router file `app/routers/web.py` to handle all user-facing web pages.

**`app/main.py` (Updated):**

```python
# ... (existing code)
from fastapi.staticfiles import StaticFiles
from app.routers import dialogue, web

# ... (lifespan function)

app = FastAPI(lifespan=lifespan)

# Mount routers
app.include_router(dialogue.router, prefix="/api/v1/dialogue", tags=["dialogue"])
app.include_router(web.router, tags=["Web"])

# Optional: Mount a directory for static files like CSS
# app.mount("/static", StaticFiles(directory="static"), name="static")
```

Notice the API is now prefixed with `/api/v1`. This is good practice to separate it from the web routes.

**Web Router (`app/routers/web.py`):**
This file will contain the logic to serve HTML pages, handle form submissions for login/registration, and manage the user dashboard.

```python
# Conceptual example of the web router
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    generate_api_token
)
from app.db import db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --- Login Endpoints ---
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def handle_login(request: Request, email: str = Form(), password: str = Form()):
    user = await db.user.find_unique(where={"email": email})
    if not user or not verify_password(password, user.hashed_password):
        # Return to login page with an error
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid email or password"})

    access_token = create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

# --- Dashboard & Token Management ---
# (This would need a dependency to get the current user from the JWT cookie)
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request): #, user: User = Depends(get_user_from_web_cookie)):
    # Fetch user and their token from DB
    # user = await db.user.find_unique(...)
    return templates.TemplateResponse("dashboard.html", {"request": request, "api_token": "user.api_token_here"})

@router.post("/dashboard/regenerate")
async def regenerate_token(request: Request): #, user: User = Depends(get_user_from_web_cookie)):
    new_token = generate_api_token()
    # await db.user.update(where={"id": user.id}, data={"api_token": new_token})
    return RedirectResponse(url="/dashboard", status_code=302)

# --- Registration logic would be similar ---
```

**HTML Templates:**
You would create simple HTML files in the `templates/` directory.

- **`login.html`**: A form with fields for `email` and `password`.
- **`dashboard.html`**: Displays the user's current API token (`Your API Token is: {{ api_token }}`) and a form with a single button to POST to `/dashboard/regenerate`.

This structure provides a complete system for users to self-manage their access to the mod's API features.
