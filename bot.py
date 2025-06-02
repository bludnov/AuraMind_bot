import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import google.generativeai as genai
from database import Database
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash-preview-05-20')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    welcome_text = """
*Привет!* 👋

Я *AuraMind* — твой ИИ-нейропсихолог. Я здесь, чтобы помочь тебе справиться со стрессом и разобраться в своих чувствах.

*Что я умею:*
• Помогать разобраться в эмоциях
• Поддерживать в трудные моменты
• Давать советы по борьбе со стрессом
• Быть рядом 24/7

*Важно:* Все наши разговоры полностью анонимны и конфиденциальны.

Чем могу помочь? 💙
"""
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    menu_text = """
*Главное меню* 📱

Выберите действие:
"""
    await message.answer(menu_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = """
*🤖 AuraMind — ваш ИИ-нейропсихолог*

*Доступные команды:*
• `/start` — Начать общение
• `/menu` — Показать главное меню
• `/help` — Показать это сообщение

*Как пользоваться:*
1. Просто напишите мне сообщение, и я отвечу
2. Используйте кнопки меню для удобной навигации
3. Я всегда готов помочь вам разобраться в чувствах и справиться со стрессом

*Важно:* 
• Все общение анонимно и конфиденциально
• Я не сохраняю историю сообщений
• Вы можете говорить со мной о любых проблемах
"""
    await message.answer(help_text, parse_mode="Markdown")

@dp.message()
async def handle_message(message: types.Message):
    if message.text == "❓ Помощь":
        await cmd_help(message)
        return

    db.add_message(message.from_user.id, message.text, is_bot=False)
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    try:
        chat_history = db.get_chat_history(message.from_user.id)
        
        chat = model.start_chat(history=[])
        
        chat.send_message(SYSTEM_PROMPT)
        
        for msg_text, is_bot, _ in chat_history:
            chat.send_message(msg_text)
        
        response = chat.send_message(message.text)
        ai_response = response.text
        
        db.add_message(message.from_user.id, ai_response, is_bot=True)
        
        await message.reply(ai_response, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error: {e}")
        error_msg = "*Произошла ошибка. Пожалуйста, попробуйте позже.* ❌"
        db.add_message(message.from_user.id, error_msg, is_bot=True)
        await message.reply(error_msg, parse_mode="Markdown")
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
