from datetime import datetime
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Хеширует пароль с использованием bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, соответствует ли открытый пароль сохранённому хешу."""
    return pwd_context.verify(plain_password, hashed_password)


def serialize_message(message):
    """Сериализует сообщение, преобразуя datetime в ISO формат."""
    message_dict = message.dict()
    for key, value in message_dict.items():
        if isinstance(value, datetime):
            message_dict[key] = value.isoformat()
    return message_dict
