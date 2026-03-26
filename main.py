import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

TOKEN = "8747129285:AAG-IXig35A1p1LTQBjEoJX2Uycr_6Uuavo"

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Хранилище
user_tasks = {}
user_state = {}
user_last_msg = {}

# Клавиатуры
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="＋ Добавить")],
        [KeyboardButton(text="≡ Список")]
    ],
    resize_keyboard=True
)

action_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✓ Готово")],
        [KeyboardButton(text="× Удалить")],
        [KeyboardButton(text="← Назад")]
    ],
    resize_keyboard=True
)

# Умная отправка (редактирует сообщение)
async def smart_send(msg: types.Message, text: str, kb=None):
    user_id = msg.from_user.id

    try:
        if user_id in user_last_msg:
            await bot.edit_message_text(
                chat_id=user_id,
                message_id=user_last_msg[user_id],
                text=text,
                reply_markup=kb
            )
        else:
            m = await msg.answer(text, reply_markup=kb)
            user_last_msg[user_id] = m.message_id
    except:
        m = await msg.answer(text, reply_markup=kb)
        user_last_msg[user_id] = m.message_id


# START
@dp.message(Command("start"))
async def start(msg: types.Message):
    user_state[msg.from_user.id] = None

    text = (
        "Приветик!!\n\n"
        "Я <b>Todox</b> — твой список задач.\n\n"
        "• Добавляй дела\n"
        "• Отмечай выполненные\n"
        "• Держи порядок\n\n"
        "<i>Начни с кнопок ниже</i>"
    )

    await smart_send(msg, text, main_kb)


# ДОБАВИТЬ
@dp.message(lambda m: m.text == "＋ Добавить")
async def add_task(msg: types.Message):
    user_state[msg.from_user.id] = "adding"
    await smart_send(msg, "Напиши задачу", None)


@dp.message(lambda m: user_state.get(m.from_user.id) == "adding")
async def save_task(msg: types.Message):
    user_id = msg.from_user.id

    user_tasks.setdefault(user_id, []).append({
        "text": msg.text,
        "done": False
    })

    user_state[user_id] = None

    await smart_send(msg, "✓ Задача успешно добавлена", main_kb)


# СПИСОК
@dp.message(lambda m: m.text == "≡ Список")
async def list_tasks(msg: types.Message):
    user_id = msg.from_user.id
    tasks = user_tasks.get(user_id, [])

    if not tasks:
        await smart_send(msg, "→ Пока пусто", main_kb)
        return

    text = "≡ <b>Твои задачи:</b>\n\n"

    for i, t in enumerate(tasks):
        status = "✓" if t["done"] else "×"
        text += f"{i+1}. {t['text']} [{status}]\n"

    text += "\n<i>Введи номер задачи</i>"

    user_state[user_id] = "choosing"
    await smart_send(msg, text, None)


# ДЕЙСТВИЕ (ВАЖНО: выше choosing)
@dp.message(lambda m: user_state.get(m.from_user.id, "").startswith("action_"))
async def task_action(msg: types.Message):
    user_id = msg.from_user.id
    tasks = user_tasks.get(user_id, [])

    if not user_state.get(user_id, "").startswith("action_"):
        return

    index = int(user_state[user_id].split("_")[1])

    if msg.text == "✓ Готово":
        tasks[index]["done"] = True
        await smart_send(msg, "✓ Отмечено как выполнено", main_kb)

    elif msg.text == "× Удалить":
        tasks.pop(index)
        await smart_send(msg, "× Задача удалена", main_kb)

    elif msg.text == "← Назад":
        user_state[user_id] = None
        await smart_send(msg, "← Возврат", main_kb)
        return

    else:
        await smart_send(msg, "→ Используй кнопки", action_kb)
        return

    user_state[user_id] = None


# ВЫБОР ЗАДАЧИ
@dp.message(lambda m: user_state.get(m.from_user.id) == "choosing" and m.text.isdigit())
async def choose_task(msg: types.Message):
    user_id = msg.from_user.id
    tasks = user_tasks.get(user_id, [])

    index = int(msg.text) - 1

    if index < 0 or index >= len(tasks):
        await smart_send(msg, "→ Такой задачи нет", None)
        return

    user_state[user_id] = f"action_{index}"

    text = (
        f"→ <b>{tasks[index]['text']}</b>\n\n"
        "Выбери действие:"
    )

    await smart_send(msg, text, action_kb)


# СТАРТ БОТА
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
