from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from core.auth import create_access_token
from core.identity import CHANNEL_ID_SEPARATOR
from core.security import SecurityManager
from database.database import get_db
from database.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    external_id: str
    password: str
    name: Optional[str] = None

    @field_validator("external_id")
    @classmethod
    def reject_channel_ids(cls, value: str) -> str:
        # IDs com ':' (ex: 'telegram:123') pertencem aos canais. Se a API aceitasse,
        # alguém poderia registrar o ID de outra pessoa antes dela falar com o bot
        # e depois ler as conversas dela.
        if CHANNEL_ID_SEPARATOR in value:
            raise ValueError(f"external_id não pode conter '{CHANNEL_ID_SEPARATOR}' (reservado aos canais).")
        return value

    @field_validator("password")
    @classmethod
    def check_password_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > SecurityManager.PASSWORD_MAX_BYTES:
            raise ValueError(f"password deve ter no máximo {SecurityManager.PASSWORD_MAX_BYTES} bytes.")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    # Qualquer usuário existente bloqueia o cadastro, inclusive os criados por um bot
    # sem senha: definir a senha deles aqui entregaria a conta (e as conversas) a quem
    # soubesse o ID. Vincular uma conta de canal exige verificar a posse, o que ainda
    # não existe.
    if db.query(User).filter(User.external_id == payload.external_id).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esse external_id já está em uso.",
        )

    user = User(
        external_id=payload.external_id,
        name=payload.name,
        hashed_password=SecurityManager.hash_password(payload.password),
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
    if not user or not user.hashed_password:
        raise invalid_credentials

    if user.password_salt:
        # Senha legada (SHA-256 + salt): confere no formato antigo e migra para bcrypt.
        if not SecurityManager.verify_hash(
            form_data.password, user.password_salt, user.hashed_password
        ):
            raise invalid_credentials
        user.hashed_password = SecurityManager.hash_password(form_data.password)
        user.password_salt = None
        db.commit()
    elif not SecurityManager.verify_password(form_data.password, user.hashed_password):
        raise invalid_credentials

    access_token = create_access_token(user.external_id)
    return TokenResponse(access_token=access_token)
