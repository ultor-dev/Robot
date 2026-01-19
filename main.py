import os
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatAction
from aiogram.filters import CommandStart
from aiogram.types import Message

from openai import OpenAI
from openai import APIError, RateLimitError, APIConnectionError

# -------------------- ENV --------------------

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Не задан TELEGRAM_BOT_TOKEN в .env")

if not OPENAI_API_KEY:
    raise RuntimeError("Не задан OPENAI_API_KEY в .env")

# -------------------- INIT --------------------

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
openai_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "Ты лаконичный и полезный ассистент. "
    "Отвечай по-русски, будь вежлив и четко структурируй ответы."
)

# -------------------- GPT --------------------

async def ask_gpt(user_text: str) -> str:
    try:
        response = openai_client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
        )

        return response.output_text or "Пустой ответ от модели."

    except RateLimitError:
        return "⚠️ Слишком много запросов. Попробуйте позже."
    except APIConnectionError:
        return "⚠️ Не удается подключиться к OpenAI. Проверьте интернет."
    except APIError as e:
        return f"⚠️ Ошибка OpenAI API: {e}"
    except Exception as e:
        return f"⚠️ Непредвиденная ошибка: {e}"

# -------------------- HANDLERS --------------------

@dp.message(CommandStart())
async def on_start(message: Message):
    await message.answer(
        "👋 Привет!\n\n"
        "Я Telegram-бот на GPT.\n"
        "Просто отправь мне сообщение — я отвечу."
    )

@dp.message(F.text & ~F.via_bot)
async def on_text(message: Message):
    await message.chat.do(ChatAction.TYPING)

    user_text = message.text.strip()
    if not user_text:
        await message.answer("Отправьте текстовое сообщение.")
        return

    reply = await ask_gpt(user_text)

    MAX_LEN = 4000
    for i in range(0, len(reply), MAX_LEN):
        await message.answer(reply[i:i + MAX_LEN])

# -------------------- MAIN --------------------

async def main():
    print("🤖 Bot is running. Press Ctrl+C to stop.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
