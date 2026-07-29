from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth import create_access_token
from core.security import SecurityManager
from database.database import get_db
from database.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    external_id: str
    password: str
    name: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    user = db.query(User).filter(User.external_id == payload.external_id).first()

    if user and user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esse external_id já possui uma senha cadastrada.",
        )

    hashed = SecurityManager.hash_sensitive_data(payload.password)

    if user:
        # Usuário já existe (criado por um bot), só está definindo a senha agora.
        user.hashed_password = hashed["hash"]
        user.password_salt = hashed["salt"]
        if payload.name:
            user.name = payload.name
    else:
        user = User(
            external_id=payload.external_id,
            name=payload.name,
            hashed_password=hashed["hash"],
            password_salt=hashed["salt"],
        )
        db.add(user)

    db.commit()

    access_token = create_access_token(payload.external_id)
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="external_id ou senha inválidos.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # form_data.username carrega o external_id (padrão OAuth2PasswordRequestForm do FastAPI).
    user = db.query(User).filter(User.external_id == form_data.username).first()
    if not user or not user.hashed_password or not user.password_salt:
        raise invalid_credentials

    if not SecurityManager.verify_hash(
        form_data.password, user.password_salt, user.hashed_password
    ):
        raise invalid_credentials

    access_token = create_access_token(user.external_id)
    return TokenResponse(access_token=access_token)
