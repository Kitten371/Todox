import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

TOKEN = "8747129285:AAG-IXig35A1p1LTQBjEoJX2Uycr_6Uuavo"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище
user_tasks = {}
user_state = {}

# Клавиатуры
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить задачу")],
        [KeyboardButton(text="📋 Список задач")]
    ],
    resize_keyboard=True
)

action_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✔️ Готово")],
        [KeyboardButton(text="🗑 Удалить")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

# START
@dp.message(Command("start"))
async def start(msg: types.Message):
    user_state[msg.from_user.id] = None
    await msg.answer(
        "Привет. Я Todox.\n\n"
        "➕ Добавляй задачи\n"
        "📋 Смотри список\n"
        "✔️ Отмечай выполненные",
        reply_markup=main_kb
    )

# ДОБАВИТЬ ЗАДАЧУ
@dp.message(lambda m: m.text == "➕ Добавить задачу")
async def add_task(msg: types.Message):
    user_state[msg.from_user.id] = "adding"
    await msg.answer("Напиши задачу.")

@dp.message(lambda m: user_state.get(m.from_user.id) == "adding")
async def save_task(msg: types.Message):
    user_id = msg.from_user.id

    user_tasks.setdefault(user_id, []).append({
        "text": msg.text,
        "done": False
    })

    user_state[user_id] = None
    await msg.answer("Задача добавлена.", reply_markup=main_kb)

# СПИСОК ЗАДАЧ
@dp.message(lambda m: m.text == "📋 Список задач")
async def list_tasks(msg: types.Message):
    user_id = msg.from_user.id
    tasks = user_tasks.get(user_id, [])

    if not tasks:
        await msg.answer("Пусто.", reply_markup=main_kb)
        return

    text = "Твои задачи:\n\n"
    for i, t in enumerate(tasks):
        status = "✔️" if t["done"] else "❌"
        text += f"{i+1}. {t['text']} [{status}]\n"

    user_state[user_id] = "choosing"
    await msg.answer(text + "\n\nНапиши номер задачи.")

# ВЫБОР ЗАДАЧИ (фикс тут)
@dp.message(lambda m: user_state.get(m.from_user.id) == "choosing" and m.text.isdigit())
async def choose_task(msg: types.Message):
    user_id = msg.from_user.id
    tasks = user_tasks.get(user_id, [])

    index = int(msg.text) - 1

    if index < 0 or index >= len(tasks):
        await msg.answer("Нет такой задачи.")
        return

    user_state[user_id] = f"action_{index}"
    await msg.answer("Выбери действие:", reply_markup=action_kb)

# ДЕЙСТВИЯ (фикс тут)
@dp.message(lambda m: user_state.get(m.from_user.id, "").startswith("action_"))
async def task_action(msg: types.Message):
    user_id = msg.from_user.id
    tasks = user_tasks.get(user_id, [])

    # защита от мусора
    if not user_state.get(user_id, "").startswith("action_"):
        return

    index = int(user_state[user_id].split("_")[1])

    if msg.text == "✔️ Готово":
        tasks[index]["done"] = True
        await msg.answer("Готово.")

    elif msg.text == "🗑 Удалить":
        tasks.pop(index)
        await msg.answer("Удалено.")

    elif msg.text == "🔙 Назад":
        user_state[user_id] = None
        await msg.answer("Назад.", reply_markup=main_kb)
        return

    else:
        await msg.answer("Выбери кнопку.")
        return

    user_state[user_id] = None
    await msg.answer("Ок.", reply_markup=main_kb)

# СТАРТ
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
