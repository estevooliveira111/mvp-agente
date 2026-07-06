import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from repositories.user_repository import UserRepository
from schemas.token import Token
from core.security import verify_password, create_access_token, get_password_hash
from schemas.user import UserForgotPassword, UserResetPassword

class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def authenticate_user(self, form_data: OAuth2PasswordRequestForm) -> Token:
        user = self.repo.get_user_by_email(form_data.username)
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(subject=user.email)
        return Token(access_token=access_token, token_type="bearer")

    def forgot_password(self, forgot_data: UserForgotPassword) -> dict:
        user = self.repo.get_user_by_email(forgot_data.email)
        if not user:
            # Prevent user enumeration
            return {"message": "If that email is in our database, we have sent a password reset token to it."}
        
        reset_token = str(uuid.uuid4())
        self.repo.set_reset_token(user, reset_token)
        
        # In a real app, send an email here. We just return the token for testing purposes.
        return {
            "message": "If that email is in our database, we have sent a password reset token to it.",
            "demo_token": reset_token  # Remove in production!
        }

    def reset_password(self, reset_data: UserResetPassword) -> dict:
        user = self.repo.get_user_by_reset_token(reset_data.token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        new_hashed = get_password_hash(reset_data.new_password)
        self.repo.update_user_password(user, new_hashed)
        self.repo.set_reset_token(user, None)  # Clear token
        
        return {"message": "Password updated successfully"}
