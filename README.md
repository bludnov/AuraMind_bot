# 🧠 AuraMind - Telegram-бот психологической поддержки

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Aiogram-3.0-2CA5E0?logo=telegram&logoColor=white" alt="Aiogram">
  <img src="https://img.shields.io/badge/Gemini-API-FF6D01?logo=google&logoColor=white" alt="Gemini">
  <img src="https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white" alt="SQLite">
</div>

## 📝 Описание проекта

Telegram-бот, предоставляющий психологическую поддержку с использованием:
- Модели Gemini AI для анализа текста
- Базы данных SQLite для хранения истории диалогов
- Библиотеки aiogram для работы с Telegram API


## 📂 Структура проекта

| Файл               | Описание                          |
|--------------------|-----------------------------------|
| `bot.py`           | Основной скрипт Telegram-бота     |
| `database.py`      | Модуль для работы с SQLite базой  |
| `requirements.txt` | Список зависимостей Python        |

## ⚙️ Технические требования

- Python 3.10+
- Аккаунт Google AI Studio (для Gemini API)
- Telegram бот-токен

## 🛠 Установка и запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте .env файл и заполните его:
```
BOT_TOKEN=your_telegram_token
GEMINI_API_KEY=your_gemini_key
SYSTEM_PROMPT=your_prompt
```

3. Запустите бота командой:
```bash
python bot.py
```

## ✨ Особенности:

- Сохранение истории диалогов
- Анализ эмоционального состояния
- Конфиденциальность данных

<div align="center"> <sub>Проект находится под MIT License/sub></div>
