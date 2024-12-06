import asyncio
from typing import Dict, List
import json

from fastapi import (
    FastAPI, Depends, WebSocket, WebSocketDisconnect,
    HTTPException, status, Request, Query)
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from db import models
from db.crud import (
        create_user, get_or_create_chat, create_message, get_messages)
from db.database import SessionLocal, engine
from db.models import User
from db.schemas import (
        UserCreate, UserOut, LoginRequest, MessageCreate, MessageOut)
from celery_tasks.tasks import send_notification_task, test_celery_task
from core.auth import (
        create_access_token, get_current_user, SECRET_KEY, ALGORITHM)
from core.utils import verify_password, serialize_message
from core.redis import redis_client
from telegram.bot import start_bot


app = FastAPI(
    title="Messaging Service API",
    description=(
        "API для обмена сообщениями в реальном времени с "
        "использованием WebSocket, Telegram-уведомлений и Celery."
    ),
    version="1.0.0",
    contact={
        "name": "Amirkhan",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }
)
models.Base.metadata.create_all(bind=engine)
connected_clients: Dict[int, List[WebSocket]] = {}
templates = Jinja2Templates(directory="/app/templates")


def get_db():
    """Создаёт и закрывает сессию базы данных для каждого запроса."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
async def get_chat_page(request: Request):
    """Отображает интерфейс чата."""
    return templates.TemplateResponse("chat.html", {"request": request})


@app.post("/register/", response_model=UserOut)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя."""
    return create_user(db=db, user=user)


@app.post("/login/")
async def login(user: LoginRequest, db: Session = Depends(get_db)):
    """Авторизация пользователя и выдача JWT-токена."""
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(
        user.password,
        db_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )

    access_token = create_access_token(user_id=db_user.id)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users")
async def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Возвращает список всех пользователей, кроме текущего."""
    return [{
        "id": user.id,
        "username": user.username
        } for user in db.query(User).filter(User.id != current_user.id).all()
    ]


@app.get("/chats/{chat_id}/messages/")
async def get_chat_messages(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получает историю сообщений для указанного чата."""
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Чат с таким ID не найден")
    if current_user.id not in {chat.user1_id, chat.user2_id}:
        raise HTTPException(status_code=403, detail="Нет доступа к чату")
    return get_messages(db=db, chat_id=chat_id)


@app.get("/chats/get_or_create/{user_id}")
async def get_or_create_chat_route(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получает или создаёт чат между текущим пользователем и
    другим пользователем.
    """
    return get_or_create_chat(
        db=db,
        user1_id=current_user.id,
        user2_id=user_id
    )


@app.delete("/chats/{chat_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Удаляет чат и все сообщения в нём."""
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    if current_user.id not in {chat.user1_id, chat.user2_id}:
        raise HTTPException(status_code=403, detail="Нет доступа к чату")
    db.query(models.Message).filter(models.Message.chat_id == chat_id).delete()
    db.delete(chat)
    db.commit()


async def get_token_data(token: str) -> int:
    """Проверяет токен и возвращает ID пользователя из payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Неверные учетные данные"
            )
        return int(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Неверный токен"
        )


@app.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: int,
    db: Session = Depends(get_db),
    token: str = Query(None)
):
    """
    WebSocket для обмена сообщениями в
    реальном времени внутри чата.
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        user_id = await get_token_data(token)
        sender = db.query(User).filter(User.id == user_id).first()
        if not sender:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        sender_name = sender.username
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()

    redis_client.sadd(f"chat:{chat_id}:users", user_id)
    redis_client.expire(f"chat:{chat_id}:users", 60)

    connected_clients.setdefault(chat_id, []).append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            redis_client.expire(f"chat:{chat_id}:users", 60)
            new_message = create_message(
                db=db,
                chat_id=chat_id,
                sender_id=user_id,
                message_data=MessageCreate(content=data)
            )
            message_out = MessageOut.from_orm(new_message)
            message_data = json.dumps(serialize_message(message_out))

            redis_client.lpush(f"chat:{chat_id}:messages", message_data)
            redis_client.ltrim(f"chat:{chat_id}:messages", 0, 49)

            for client in connected_clients[chat_id]:
                try:
                    await client.send_text(message_data)
                except WebSocketDisconnect:
                    connected_clients[chat_id].remove(client)
                    redis_client.srem(f"chat:{chat_id}:users", user_id)

            chat_participants = [
                new_message.chat.user1_id,
                new_message.chat.user2_id
            ]
            for participant_id in chat_participants:
                if participant_id != user_id:
                    recipient = db.query(User).filter(
                        User.id == participant_id).first()
                    if recipient and recipient.telegram_id:
                        notification_text = (
                            f"Новое сообщение от {sender_name}: {data}"
                        )
                        send_notification_task.delay(
                                recipient.telegram_id,
                                notification_text
                        )

    except WebSocketDisconnect:
        redis_client.srem(f"chat:{chat_id}:users", user_id)
        connected_clients[chat_id].remove(websocket)
        if not connected_clients[chat_id]:
            del connected_clients[chat_id]


async def cleanup_inactive_chats():
    """Фоновая задача для очистки неактивных чатов в Redis."""
    while True:
        print("Запуск фоновой очистки...")
        chat_keys = redis_client.keys("chat:*:users")

        for chat_key in chat_keys:
            ttl = redis_client.ttl(chat_key)
            if ttl == -2:
                chat_id = chat_key.split(":")[1]
                print(f"Чат {chat_id} удален из Redis.")
                redis_client.delete(f"chat:{chat_id}:messages")

        await asyncio.sleep(600)


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(start_bot())
    asyncio.create_task(cleanup_inactive_chats())


@app.get("/test_celery/")
async def test_celery():
    test_celery_task.delay()
    return {"status": "Тестовая задача отправлена в Celery"}
