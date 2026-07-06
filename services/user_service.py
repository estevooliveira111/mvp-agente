from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from repositories.user_repository import UserRepository
from schemas.user import UserCreate, UserUpdate, UserUpdatePassword
from models.user import User
from core.security import verify_password, get_password_hash

class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def register_user(self, user_in: UserCreate) -> User:
        user = self.repo.get_user_by_email(user_in.email)
        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered."
            )
        return self.repo.create_user(user_in)

    def get_user_by_id(self, user_id: int) -> User:
        user = self.repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    def update_user(self, current_user: User, user_in: UserUpdate) -> User:
        if user_in.email and user_in.email != current_user.email:
            existing_user = self.repo.get_user_by_email(user_in.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken by another user."
                )
        return self.repo.update_user(current_user, user_in)

    def change_password(self, current_user: User, password_in: UserUpdatePassword) -> User:
        if not verify_password(password_in.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password."
            )
        new_hashed = get_password_hash(password_in.new_password)
        return self.repo.update_user_password(current_user, new_hashed)
