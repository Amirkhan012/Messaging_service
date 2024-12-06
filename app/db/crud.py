from sqlalchemy.orm import Session

from db.models import User, Chat, Message
from db.schemas import UserCreate, MessageCreate
from core.utils import hash_password


def create_user(db: Session, user: UserCreate) -> User:
    """Создаёт нового пользователя в базе данных."""
    hashed_password = hash_password(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_or_create_chat(db: Session, user1_id: int, user2_id: int) -> Chat:
    """Находит существующий чат между двумя пользователями или
    создаёт новый.
    """
    chat = db.query(Chat).filter(
        ((Chat.user1_id == user1_id) & (Chat.user2_id == user2_id)) |
        ((Chat.user1_id == user2_id) & (Chat.user2_id == user1_id))
    ).first()
    if not chat:
        chat = Chat(user1_id=user1_id, user2_id=user2_id)
        db.add(chat)
        db.commit()
        db.refresh(chat)
    return chat


def create_message(
    db: Session,
    chat_id: int,
    sender_id: int,
    message_data: MessageCreate
) -> Message:
    """Создаёт новое сообщение и сохраняет его в базе данных."""
    db_message = Message(
        chat_id=chat_id,
        sender_id=sender_id,
        content=message_data.content
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_messages(db: Session, chat_id: int):
    """Возвращает сообщения для определённого чата,
    отсортированные по времени.
    """
    return db.query(Message).filter(
        Message.chat_id == chat_id).order_by(Message.timestamp).all()
