import os
import aiohttp
import ffmpeg
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import openai
from pydantic import BaseModel

# 🔹 Загружаем API-ключи из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("7899586060:AAHtuIWtfCYqP5tNB4KZUVh_A43bWwBhK60")
OPENAI_API_KEY = os.getenv("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")

# 🔹 Создаем бота и диспетчер
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# ✅ Модель для ChatGPT
class ChatGPTRequest(BaseModel):
    model: str = "gpt-4"
    messages: list

# ✅ Обработчик команды /start
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Я работаю через Webhook и могу распознавать голосовые сообщения.")

# ✅ Обработчик голосовых сообщений
@dp.message(types.Voice)
async def voice_message_handler(message: Message):
    await message.answer("⏳ Распознаю голосовое сообщение...")

    # 🔹 Получаем ссылку на голосовой файл
    file = await bot.get_file(message.voice.file_id)
    file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file.file_path}"

    # 🔹 Скачиваем голосовой файл
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            if resp.status == 200:
                with open("voice.ogg", "wb") as f:
                    f.write(await resp.read())

    # 🔹 Конвертируем в MP3
    input_file = "voice.ogg"
    output_file = "voice.mp3"
    ffmpeg.input(input_file).output(output_file, format="mp3").run(overwrite_output=True)

    # 🔹 Распознаем текст через Whisper API
    with open(output_file, "rb") as f:
        response = openai.Audio.transcribe(
            model="whisper-1",
            file=f,
            api_key=OPENAI_API_KEY
        )
        text = response["text"]

    await message.answer(f"📌 Распознанный текст: {text}")

    # 🔹 Отправляем текст в ChatGPT
    chat_request = ChatGPTRequest(messages=[{"role": "user", "content": text}])
    chat_response = openai.ChatCompletion.create(
        model=chat_request.model,
        messages=chat_request.messages,
        api_key=OPENAI_API_KEY
    )
    answer = chat_response["choices"][0]["message"]["content"]

    await message.answer(answer)

# ✅ Устанавливаем Webhook
async def on_startup(bot: Bot):
    webhook_url = "https://chatbot-btc4.onrender.com/webhook"  # Укажите ваш Render URL
    await bot.set_webhook(webhook_url)

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

# ✅ Запуск Aiohttp Web Server для Webhook
app = web.Application()
webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
webhook_handler.register(app, path="/webhook")
setup_application(app, dp, bot=bot)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8000)
