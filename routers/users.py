from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.deps import get_current_user
from database.database import get_db
from services.user_service import UserService
from schemas.user import UserOut, UserUpdate, UserUpdatePassword
from models.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user."""
    return current_user

@router.put("/me", response_model=UserOut)
def update_me(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update details of the currently authenticated user."""
    user_service = UserService(db)
    return user_service.update_user(current_user, user_in)

@router.put("/me/change-password", response_model=UserOut)
def change_password(
    password_in: UserUpdatePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Change password for the currently authenticated user."""
    user_service = UserService(db)
    return user_service.change_password(current_user, password_in)
