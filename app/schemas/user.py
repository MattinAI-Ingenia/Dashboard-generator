# schemas/user.py
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

# Schemas
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True
