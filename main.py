import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

TOKEN = "ТВОЙ_ТОКЕН"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище задач (пока в памяти)
user_tasks = {}

# Клавиатура
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить задачу")],
        [KeyboardButton(text="📋 Список задач")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer(
        "Привет. Я Todox.\n\n"
        "Я помогу тебе не развалить свою жизнь (хотя бы список дел).\n\n"
        "Ты можешь:\n"
        "➕ Добавлять задачи\n"
        "📋 Смотреть список\n"
        "✔️ Отмечать выполненные\n\n"
        "Начни с кнопок ниже.",
        reply_markup=main_kb
    )

@dp.message(lambda msg: msg.text == "➕ Добавить задачу")
async def add_task(msg: types.Message):
    await msg.answer("Пиши задачу. Без философии, просто текст.")

    @dp.message()
    async def save_task(m: types.Message):
        user_id = m.from_user.id
        user_tasks.setdefault(user_id, []).append({
            "text": m.text,
            "done": False
        })

        await m.answer("Задача сохранена. Поздравляю, ты стал чуть менее бесполезным.")
        
        dp.message.handlers.pop()  # убираем временный хендлер

@dp.message(lambda msg: msg.text == "📋 Список задач")
async def list_tasks(msg: types.Message):
    user_id = msg.from_user.id
    tasks = user_tasks.get(user_id, [])

    if not tasks:
        await msg.answer("У тебя пусто. Либо ты идеален, либо ленив.")
        return

    text = "Твои задачи:\n\n"
    for i, t in enumerate(tasks):
        status = "✔️" if t["done"] else "❌"
        text += f"{i+1}. {t['text']} [{status}]\n"

    await msg.answer(text + "\n\nНапиши номер задачи чтобы изменить.")

    @dp.message()
    async def manage_task(m: types.Message):
        if not m.text.isdigit():
            return

        index = int(m.text) - 1
        if index >= len(tasks):
            await m.answer("Такой задачи нет.")
            return

        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✔️ Готово")],
                [KeyboardButton(text="🗑 Удалить")]
            ],
            resize_keyboard=True
        )

        await m.answer("Выбери действие:", reply_markup=kb)

        @dp.message()
        async def action(a: types.Message):
            if a.text == "✔️ Готово":
                tasks[index]["done"] = True
                await a.answer("Отмечено. Ты сделал хоть что-то.")
            elif a.text == "🗑 Удалить":
                tasks.pop(index)
                await a.answer("Удалено. Как будто этого и не было.")

            dp.message.handlers.pop()

        dp.message.handlers.append(action)

    dp.message.handlers.append(manage_task)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
