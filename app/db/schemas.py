from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Схема для регистрации нового пользователя."""
    username: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    """Схема для отображения данных пользователя при ответе."""
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Схема для входа пользователя."""
    username: str
    password: str


class ChatOut(BaseModel):
    """Схема для отображения данных чата."""
    id: int
    user1_id: int
    user2_id: int

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Схема для создания сообщения."""
    content: str


class MessageOut(BaseModel):
    """Схема для отображения данных сообщения."""
    id: int
    chat_id: int
    sender_id: int
    content: str
    timestamp: datetime

    class Config:
        from_attributes = True
