import os
import openai
import asyncio
import aiohttp
import ffmpeg
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command

# Подставьте свои API-ключи
TELEGRAM_BOT_TOKEN = "7899586060:AAHtuIWtfCYqP5tNB4KZUVh_A43bWwBhK60"
OPENAI_API_KEY = "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"

# Инициализация бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Я бот с ChatGPT. Напиши текст или отправь голосовое сообщение, и я его формализую!")

# Функция для загрузки и конвертации голосового сообщения
async def convert_voice(voice: types.Voice):
    file = await bot.get_file(voice.file_id)
    file_path = file.file_path

    # Загружаем файл
    file_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            if resp.status == 200:
                with open("voice.ogg", "wb") as f:
                    f.write(await resp.read())

    # Конвертируем в MP3 (Whisper API поддерживает mp3, wav, m4a)
    input_file = "voice.ogg"
    output_file = "voice.mp3"
    ffmpeg.input(input_file).output(output_file, format="mp3").run(overwrite_output=True)

    return output_file

# Обработчик голосовых сообщений
@dp.message(types.Voice)
async def voice_message_handler(message: Message):
    await message.answer("Распознаю и формализую голосовое сообщение...")

    # Конвертируем голос в текст
    audio_file = await convert_voice(message.voice)
    with open(audio_file, "rb") as f:
        response = openai.Audio.transcribe(
            model="whisper-1",
            file=f,
            api_key=OPENAI_API_KEY
        )
        text = response["text"]

    # Формализуем текст с помощью ChatGPT
    formatted_prompt = f"""
    Ты — помощник, который формализует текст. Преобразуй данный текст в структурированный формат:
    
    1. Выдели главные идеи.
    2. Создай краткое резюме.
    3. Представь информацию в виде списка, если это возможно.
    
    Исходный текст: {text}
    """

    chat_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": formatted_prompt}],
        api_key=OPENAI_API_KEY
    )
    formatted_answer = chat_response["choices"][0]["message"]["content"]

    await message.answer(f"📌 **Формализованный текст:**\n{formatted_answer}")

# Обработчик текстовых сообщений
@dp.message()
async def chat_with_gpt(message: Message):
    formatted_prompt = f"""
    Ты — помощник, который формализует текст. Преобразуй данный текст в структурированный формат:
    
    1. Выдели главные идеи.
    2. Создай краткое резюме.
    3. Представь информацию в виде списка, если это возможно.
    
    Исходный текст: {message.text}
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": formatted_prompt}],
        api_key=OPENAI_API_KEY
    )
    formatted_answer = response["choices"][0]["message"]["content"]

    await message.answer(f"📌 **Формализованный текст:**\n{formatted_answer}")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
