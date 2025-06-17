import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import requests
from database import Database
from subscription_db import SubscriptionDB
from dotenv import load_dotenv
import os
import sys

load_dotenv()

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

BOT_TOKEN = os.getenv("BOT_TOKEN")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_KEY")

LOCAL_API_URL = os.getenv("API_URL")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS").split(",")]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Database()
sub_db = SubscriptionDB()

user_settings = {}

admin_states = {}

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="🎁 Попробовать бесплатно")],
            [KeyboardButton(text="🔑 Активировать ключ")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_settings_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Выбрать возраст", callback_data="age")],
            [InlineKeyboardButton(text="Стиль ответов", callback_data="style")],
            [InlineKeyboardButton(text="Давать советы", callback_data="advice")],
            [InlineKeyboardButton(text="Пол бота", callback_data="bot_gender")],
            [InlineKeyboardButton(text="Мой пол", callback_data="user_gender")],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_main")]
        ]
    )
    return keyboard

def get_age_keyboard(user_id):
    current_age = user_settings[user_id]["age"] if user_id in user_settings else None
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'✅ ' if current_age == '13-18' else ''}13-18 лет",
                callback_data="age_13_18"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if current_age == '19-35' else ''}19-35 лет",
                callback_data="age_19_35"
            )],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_settings")]
        ]
    )
    return keyboard

def get_style_keyboard(user_id):
    current_style = user_settings[user_id]["style"] if user_id in user_settings else "short"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'✅ ' if current_style == 'short' else ''}Кратко",
                callback_data="style_short"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if current_style == 'long' else ''}Развёрнуто",
                callback_data="style_long"
            )],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_settings")]
        ]
    )
    return keyboard

def get_advice_keyboard(user_id):
    current_advice = user_settings[user_id]["advice"] if user_id in user_settings else False
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'✅ ' if current_advice else ''}Да",
                callback_data="advice_yes"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if not current_advice else ''}Нет",
                callback_data="advice_no"
            )],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_settings")]
        ]
    )
    return keyboard

def get_bot_gender_keyboard(user_id):
    current_bot_gender = user_settings[user_id]["bot_gender"] if user_id in user_settings else None
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'✅ ' if current_bot_gender == 'female' else ''}Женский",
                callback_data="bot_gender_female"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if current_bot_gender == 'male' else ''}Мужской",
                callback_data="bot_gender_male"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if current_bot_gender == 'neutral' else ''}Нейтральный",
                callback_data="bot_gender_neutral"
            )],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_settings")]
        ]
    )
    return keyboard

def get_user_gender_keyboard(user_id):
    current_user_gender = user_settings[user_id]["user_gender"] if user_id in user_settings else None
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{'✅ ' if current_user_gender == 'female' else ''}Женский",
                callback_data="user_gender_female"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if current_user_gender == 'male' else ''}Мужской",
                callback_data="user_gender_male"
            )],
            [InlineKeyboardButton(
                text=f"{'✅ ' if current_user_gender == 'neutral' else ''}Нейтральный",
                callback_data="user_gender_neutral"
            )],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_settings")]
        ]
    )
    return keyboard

def get_admin_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать ключ", callback_data="admin_create_key")],
            [InlineKeyboardButton(text="➖ Удалить ключ", callback_data="admin_delete_key")],
            [InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_main")]
        ]
    )
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    user_settings[user_id] = {
        "age": None,
        "style": "short",
        "advice": False,
        "bot_gender": "neutral",
        "user_gender": "neutral"
    }
    
    db.add_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        bot_gender="neutral",
        user_gender="neutral"
    )
    sub_db.add_user(user_id)
    
    welcome_text = """
*Привет!* 👋 
Я *AuraMind*. Здесь ты можешь спокойно и безопасно поделиться всем, что тебя волнует. Я не даю советов, но помогу тебе разобраться в твоих мыслях. Начну с того, что спрошу: что сейчас происходит в твоей жизни, что привело тебя сюда? 💙

Настройки необязательны, но вы можете настроить бота под себя в меню "⚙️ Настройки"

🎁 Попробуйте бесплатный период на 3 дня!

🔑 Активируйте премиум-подписку с помощью ключа!
"""
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message(Command("menu"))
async def cmd_menu(message: types.Message):
    menu_text = """
*Главное меню* 📱

Выберите действие:
"""
    await message.answer(menu_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        await message.answer(
            "*Панель администратора* 🔒\n\nВыберите действие:",
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard()
        )
    else:
        await message.reply("У вас нет доступа к этой команде.")

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = """
*🕊️ AuraMind — ваш ИИ-психолог*

• Все общение анонимно и конфиденциально
• Вы можете говорить со мной о любых проблемах
• Телефон доверия для детей и подростков: 8-800-2000-122
"""
    await message.answer(help_text, parse_mode="Markdown")

@dp.callback_query()
async def process_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id not in user_settings:
        user_settings[user_id] = {
            "age": None,
            "style": "short",
            "advice": False,
            "bot_gender": None,
            "user_gender": None
        }

    if callback_query.data == "age":
        await callback_query.message.edit_text(
            "Выберите ваш возраст:",
            reply_markup=get_age_keyboard(user_id)
        )
    elif callback_query.data.startswith("age_"):
        age_range = callback_query.data.split("_")[1:]
        user_settings[user_id]["age"] = f"{age_range[0]}-{age_range[1]}"
        await callback_query.message.edit_text(
            "Выберите ваш возраст:",
            reply_markup=get_age_keyboard(user_id)
        )
    elif callback_query.data == "style":
        await callback_query.message.edit_text(
            "Выберите стиль ответов:",
            reply_markup=get_style_keyboard(user_id)
        )
    elif callback_query.data.startswith("style_"):
        style = callback_query.data.split("_")[1]
        user_settings[user_id]["style"] = style
        await callback_query.message.edit_text(
            "Выберите стиль ответов:",
            reply_markup=get_style_keyboard(user_id)
        )
    elif callback_query.data == "advice":
        await callback_query.message.edit_text(
            "Хотите ли вы получать советы?",
            reply_markup=get_advice_keyboard(user_id)
        )
    elif callback_query.data.startswith("advice_"):
        advice = callback_query.data.split("_")[1] == "yes"
        user_settings[user_id]["advice"] = advice
        await callback_query.message.edit_text(
            "Хотите ли вы получать советы?",
            reply_markup=get_advice_keyboard(user_id)
        )
    elif callback_query.data == "bot_gender":
        await callback_query.message.edit_text(
            "Выберите пол бота:",
            reply_markup=get_bot_gender_keyboard(user_id)
        )
    elif callback_query.data.startswith("bot_gender_"):
        bot_gender = callback_query.data.split("_")[2]
        user_settings[user_id]["bot_gender"] = bot_gender
        db.update_user_setting(user_id, "bot_gender", bot_gender)
        await callback_query.message.edit_text(
            "Выберите пол бота:",
            reply_markup=get_bot_gender_keyboard(user_id)
        )
    elif callback_query.data == "user_gender":
        await callback_query.message.edit_text(
            "Укажите ваш пол:",
            reply_markup=get_user_gender_keyboard(user_id)
        )
    elif callback_query.data.startswith("user_gender_"):
        user_gender = callback_query.data.split("_")[2]
        user_settings[user_id]["user_gender"] = user_gender
        db.update_user_setting(user_id, "user_gender", user_gender)
        await callback_query.message.edit_text(
            "Укажите ваш пол:",
            reply_markup=get_user_gender_keyboard(user_id)
        )
    elif callback_query.data == "back_to_settings":
        await callback_query.message.edit_text(
            "⚙️ Настройки",
            reply_markup=get_settings_keyboard()
        )
    elif callback_query.data == "back_to_main":
        await callback_query.message.delete()
        await callback_query.message.answer(
            "Настройки сохранены",
            reply_markup=get_main_keyboard()
        )
    elif callback_query.data == "admin_create_key":
        if user_id in ADMIN_IDS:
            new_key = sub_db.create_activation_key()
            await callback_query.message.answer(f"🔑 Новый ключ активации: `{new_key}`", parse_mode="Markdown")
        else:
            await callback_query.answer("У вас нет доступа к этой функции.")
    elif callback_query.data == "admin_delete_key":
        if user_id in ADMIN_IDS:
            admin_states[user_id] = "waiting_for_key_to_delete"
            await callback_query.message.answer("Введите ключ, который хотите удалить:")
        else:
            await callback_query.answer("У вас нет доступа к этой функции.")

@dp.message()
async def handle_message(message: types.Message):
    user_id = message.from_user.id

    if user_id in ADMIN_IDS and admin_states.get(user_id) == "waiting_for_key_to_delete":
        key_to_delete = message.text.strip()
        if sub_db.delete_activation_key(key_to_delete):
            await message.answer(f"Ключ `{key_to_delete}` успешно удален.", parse_mode="Markdown")
        else:
            await message.answer(f"Не удалось удалить ключ `{key_to_delete}`. Возможно, его не существует или он уже использован.", parse_mode="Markdown")
        admin_states.pop(user_id, None) 
        return

    if message.text == "❓ Помощь":
        await cmd_help(message)
        return
    elif message.text == "⚙️ Настройки":
        await message.answer(
            "⚙️ Настройки",
            reply_markup=get_settings_keyboard()
        )
        return
    elif message.text == "🎁 Попробовать бесплатно":
        user_id = message.from_user.id
        if sub_db.activate_trial(user_id):
            days_left = sub_db.get_trial_days_left(user_id)
            await message.answer(
                f"🎉 Поздравляем! Вам активирован бесплатный период на {days_left} дней!",
                reply_markup=get_main_keyboard()
            )
        else:
            await message.answer(
                "❌ К сожалению, вы уже использовали бесплатный период. Приобретите премиум-подписку для продолжения использования.",
                reply_markup=get_main_keyboard()
            )
        return
    elif message.text == "🔑 Активировать ключ":
        await message.answer("Пожалуйста, введите ваш ключ активации. Например: `/activate ВАШ_КЛЮЧ`", parse_mode="Markdown")
        return
    elif message.text and message.text.startswith("/activate "):
        activation_key = message.text.split(" ", 1)[1].strip()
        if sub_db.activate_premium(user_id, activation_key):
            await message.answer("✅ Ваш премиум-доступ успешно активирован!", reply_markup=get_main_keyboard())
        else:
            await message.answer("❌ Неверный ключ активации или он уже использован.", reply_markup=get_main_keyboard())
        return

    try:
        if not sub_db.check_subscription(user_id):
            await message.answer(
                "❌ У вас нет активной подписки. Активируйте бесплатный период или приобретите премиум-подписку.",
                reply_markup=get_main_keyboard()
            )
            return

        if user_id not in user_settings:
            user_settings[user_id] = {
                "age": None,
                "style": "short",
                "advice": False,
                "bot_gender": None,
                "user_gender": None
            }
        
        db_settings = db.get_user_settings(user_id)
        if db_settings:
            user_settings[user_id]["bot_gender"] = db_settings[0]
            user_settings[user_id]["user_gender"] = db_settings[1]

        db.add_message(user_id, message.text, is_bot=False)
        await bot.send_chat_action(chat_id=message.chat.id, action="typing")
        
        chat_history = db.get_chat_history(user_id)
        
        prompt = ""
        if SYSTEM_PROMPT:
            prompt += f"{SYSTEM_PROMPT}\n\n"
            
        settings = user_settings[user_id]
        prompt += f"О пользователе:\n"
        if settings["age"]:
            prompt += f"Возраст: {settings['age']}\n"
        if settings["style"]:
            prompt += f"Он хочет чтобы ты отвечал: {'Кратко' if settings['style'] == 'short' else 'Развёрнуто'}\n"
        if settings["advice"] is not None:
            prompt += f"Хочет ли он чтобы ты давал советы: {'Да' if settings['advice'] else 'Нет'}\n"
            
        if settings["bot_gender"]:
            bot_gender_ru = "женский" if settings["bot_gender"] == "female" else \
                            "мужской" if settings["bot_gender"] == "male" else \
                            "нейтральный"
            prompt += f"Пол бота: {bot_gender_ru}\n"
            
        if settings["user_gender"]:
            user_gender_ru = "женский" if settings["user_gender"] == "female" else \
                             "мужской" if settings["user_gender"] == "male" else \
                             "нейтральный"
            prompt += f"Пол пользователя: {user_gender_ru}\n"

        if settings["bot_gender"] == "neutral" or settings["user_gender"] == "neutral":
            prompt += "Составляй ответы так, чтобы не был понятен твой пол и пол собеседника.\n"

        prompt += "\n"

        for msg_text, is_bot, _ in chat_history[-5:]:
            role = "Ассистент" if is_bot else "Пользователь"
            prompt += f"{role}: {msg_text}\n"
        
        prompt += f"Пользователь: {message.text}\nАссистент:"
        
        try:
            response = requests.post(
                f"{LOCAL_API_URL}/v1/completions",
                json={
                    "model": "google/gemma-3-12b",
                    "prompt": prompt,
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "top_p": 0.9,
                    "frequency_penalty": 0.0,
                    "presence_penalty": 0.0,
                    "stop": ["Пользователь:", "Система:"]
                },
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                timeout=10
            )
            
            if response.status_code != 200:
                raise Exception(f"Local API returned {response.status_code}")
                
        except Exception as e:
            logging.warning(f"Local API failed, falling back to DeepSeek: {str(e)}")
            response = requests.post(
                DEEPSEEK_API_URL,
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT if SYSTEM_PROMPT else ""},
                        {"role": "user", "content": message.text}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
                }
            )
        
        if response.status_code == 200:
            response_data = response.json()
            
            if "choices" in response_data and len(response_data["choices"]) > 0:
                if "text" in response_data["choices"][0]:
                    full_response = response_data["choices"][0]["text"].strip()
                else:
                    full_response = response_data["choices"][0]["message"]["content"].strip()
                
                if full_response:
                    parts = full_response.split("Ассистент:", 1)
                    ai_response = parts[-1].strip() if len(parts) > 1 else full_response
                    logging.info(f"Финальный ответ ИИ: {ai_response}")
                    db.add_message(user_id, ai_response, is_bot=True)
                    ai_response = ai_response.replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace('`', '\\`')
                    await message.reply(ai_response, parse_mode="Markdown")
                    return
                else:
                    raise Exception("Пустой ответ от модели")
            else:
                raise Exception("Нет вариантов ответа")
        else:
            raise Exception(f"API вернул код {response.status_code}: {response.text}")
            
    except Exception as e:
        logging.error(f"Детали ошибки: {str(e)}")
        error_msg = "*Произошла ошибка. Пожалуйста, попробуйте позже.* ❌"
        db.add_message(message.from_user.id, error_msg, is_bot=True)
        await message.reply(error_msg, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
