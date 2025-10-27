# app/repositories/user.py
from typing import Optional
from sqlalchemy.orm import Session
from db.models import User

class UserRepository:
    """Repository for user operations"""
    
    def get_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    def create(self, db: Session, email: str, password_hash: str, name: str) -> User:
        """Create new user"""
        user = User(
            email=email,
            password_hash=password_hash,
            name=name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

user_repository = UserRepository()