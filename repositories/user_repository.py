from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate, UserUpdate
from core.security import get_password_hash
from typing import Optional

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_reset_token(self, token: str) -> Optional[User]:
        return self.db.query(User).filter(User.reset_token == token).first()

    def create_user(self, user: UserCreate) -> User:
        db_user = User(
            name=user.name,
            email=user.email,
            hashed_password=get_password_hash(user.password)
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update_user(self, user: User, user_update: UserUpdate) -> User:
        if user_update.name is not None:
            user.name = user_update.name
        if user_update.email is not None:
            user.email = user_update.email
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user_password(self, user: User, new_password_hash: str) -> User:
        user.hashed_password = new_password_hash
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def set_reset_token(self, user: User, token: Optional[str]) -> User:
        user.reset_token = token
        self.db.commit()
        self.db.refresh(user)
        return user
