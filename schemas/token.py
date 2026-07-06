from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

from typing import Optional

class TokenData(BaseModel):
    email: Optional[str] = None
