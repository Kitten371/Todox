import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

TOKEN = "8747129285:AAG-IXig35A1p1LTQBjEoJX2Uycr_6Uuavo"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище задач
user_tasks = {}

# Клавиатура
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить задачу")],
        [KeyboardButton(text="📋 Список задач")]
    ],
    resize_keyboard=True
)

# Состояния
class TaskStates(StatesGroup):
    adding_task = State()
    managing_task = State()

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
async def add_task(msg: types.Message, state: FSMContext):
    await msg.answer("Пиши задачу. Без философии, просто текст.")
    await state.set_state(TaskStates.adding_task)

@dp.message(TaskStates.adding_task)
async def save_task(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    user_tasks.setdefault(user_id, []).append({
        "text": msg.text,
        "done": False
    })
    
    await msg.answer("Задача сохранена. Поздравляю, ты стал чуть менее бесполезным.")
    await state.clear()

@dp.message(lambda msg: msg.text == "📋 Список задач")
async def list_tasks(msg: types.Message, state: FSMContext):
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
    await state.set_state(TaskStates.managing_task)

@dp.message(TaskStates.managing_task)
async def manage_task(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    tasks = user_tasks.get(user_id, [])
    
    if not msg.text.isdigit():
        await msg.answer("Напиши номер задачи (только цифры).")
        return
    
    index = int(msg.text) - 1
    if index < 0 or index >= len(tasks):
        await msg.answer("Такой задачи нет.")
        return
    
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✔️ Готово")],
            [KeyboardButton(text="🗑 Удалить")]
        ],
        resize_keyboard=True
    )
    
    await msg.answer("Выбери действие:", reply_markup=kb)
    await state.update_data(task_index=index)

@dp.message(TaskStates.managing_task, lambda msg: msg.text in ["✔️ Готово", "🗑 Удалить"])
async def action(msg: types.Message, state: FSMContext):
    user_id = msg.from_user.id
    tasks = user_tasks.get(user_id, [])
    data = await state.get_data()
    index = data.get("task_index")
    
    if index is None or index < 0 or index >= len(tasks):
        await msg.answer("Что-то пошло не так. Попробуй ещё раз.")
        await state.clear()
        return
    
    if msg.text == "✔️ Готово":
        tasks[index]["done"] = True
        await msg.answer("Отмечено. Ты сделал хоть что-то.")
    elif msg.text == "🗑 Удалить":
        tasks.pop(index)
        await msg.answer("Удалено. Как будто этого и не было.")
    
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
