"""User Schemas"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    """Schema for user registration"""
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, description="Password min 6 characters")
    
    model_config = {
        "json_schema_extra" : {
            "examples": [{
                "username": "john_doe",
                "email": "john@example.com",
                "password": "securepassword123"
            }]
        }
    }
    
    
class UserResponse(BaseModel):
    """Schema for user information response"""
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }
    
class Token(BaseModel):
    """Schema for JWT for token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    
class TokenData(BaseModel):
    """Schmea for decoded token data"""
    username: Optional[str] = None