from datetime import timedelta
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_user
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models import Users
from pydantic import BaseModel, EmailStr

router = APIRouter(tags=["Auth"])

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

@router.post("/register", response_model=dict)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user with this email already exists
    existing_user = db.query(Users).filter(Users.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user with hashed password
    db_user = Users(
        name=user.name,
        email=user.email,
        password=get_password_hash(user.password)
    )
    
    # Add and commit to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"message": "User registered successfully"}

class UserLogin(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    # Find user by email (form_data.username will contain the email)
    user = db.query(Users).filter(Users.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
   
    # Verify password
    if not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
   
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )
   
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }

@router.get("/test-token", response_model=dict)
async def test_token(current_user: Users = Depends(get_current_user)):
    return {
        "message": "Token is valid",
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email
        }
    }

