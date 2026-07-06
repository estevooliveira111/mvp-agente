from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database.database import get_db
from services.auth_service import AuthService
from services.user_service import UserService
from schemas.user import UserCreate, UserOut, UserForgotPassword, UserResetPassword
from schemas.token import Token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    user_service = UserService(db)
    return user_service.register_user(user_in)

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login to get an access token."""
    auth_service = AuthService(db)
    return auth_service.authenticate_user(form_data)

@router.post("/forgot-password")
def forgot_password(forgot_data: UserForgotPassword, db: Session = Depends(get_db)):
    """Request a password reset token."""
    auth_service = AuthService(db)
    return auth_service.forgot_password(forgot_data)

@router.post("/reset-password")
def reset_password(reset_data: UserResetPassword, db: Session = Depends(get_db)):
    """Reset password using a token."""
    auth_service = AuthService(db)
    return auth_service.reset_password(reset_data)
