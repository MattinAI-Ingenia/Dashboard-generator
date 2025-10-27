# app/api/routers/user.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime
import logging

from core.database import get_db
from schemas.user import UserSignup, UserLogin, UserResponse
from repositories.user import user_repository

router = APIRouter()
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    # Check if user exists
    if user_repository.get_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    password_hash = pwd_context.hash(user_data.password)
    
    # Create user
    user = user_repository.create(db, user_data.email, password_hash, user_data.name)
    
    logger.info(f"New user created: {user.email}")
    return user

@router.post("/login", response_model=UserResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    # Find user
    user = user_repository.get_by_email(db, credentials.email)
    
    if not user or not pwd_context.verify(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    user.login = datetime.now()
    db.commit()
    
    logger.info(f"User logged in: {user.email}")
    return user
