import logging

from aiogram import Bot
from asgiref.sync import async_to_sync
from celery import shared_task

from celery_config import celery_app
from telegram.bot import API_TOKEN

logger = logging.getLogger(__name__)


@shared_task
def send_notification_task(telegram_id: int, message: str):
    """
    Синхронная задача для отправки уведомления через Telegram.
    """
    try:
        print(
            "[Telegram Notification] Отправка сообщения Telegram ID: "
            f"{telegram_id}, текст: {message}"
        )

        async def send_message():
            async with Bot(token=API_TOKEN) as bot:
                await bot.send_message(chat_id=telegram_id, text=message)

        async_to_sync(send_message)()

        return (
            "Уведомление успешно отправлено пользователю с "
            f"Telegram ID {telegram_id}"
        )
    except Exception as e:
        print(f"[Telegram Notification] Ошибка при отправке сообщения: {e}")
        raise


@celery_app.task
def test_celery_task():
    print("Тестовая задача Celery выполнена.")
    return "OK"
