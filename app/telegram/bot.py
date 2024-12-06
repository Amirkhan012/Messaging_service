from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from db.database import SessionLocal
from db.models import User
from core.config import settings

API_TOKEN = settings.TELEGRAM_TOKEN

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Привет! Отправь свой email для привязки к аккаунту.")


@dp.message(lambda message: "@" in message.text)
async def handle_email_verification(message: Message):
    email = message.text.strip()

    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()

        if user:
            user.telegram_id = message.from_user.id
            db.commit()
            await message.reply(f"Ваш email {email} был привязан.")
        else:
            await message.reply(
                "Email не найден. Пожалуйста, убедитесь,"
                "что вы зарегистрированы."
            )


async def start_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, skip_updates=True)
