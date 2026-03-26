import asyncio
import time
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

TOKEN = "8747129285:AAG-IXig35A1p1LTQBjEoJX2Uycr_6Uuavo"
ADMIN_ID = 5893181200

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Хранилища
user_tasks = {}
user_state = {}
user_last_msg = {}
users_db = {}

# Обновление активности
def update_user(user_id):
    users_db[user_id] = int(time.time())

# Клавиатуры
def get_main_kb(user_id):
    if user_id == ADMIN_ID:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="＋ Добавить")],
                [KeyboardButton(text="≡ Список")],
                [KeyboardButton(text="⚙ Админ")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
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

admin_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📢 Рассылка")],
        [KeyboardButton(text="👥 Пользователи")],
        [KeyboardButton(text="← Назад")]
    ],
    resize_keyboard=True
)

# Умная отправка
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
    user_id = msg.from_user.id
    update_user(user_id)
    user_state[user_id] = None

    text = (
        "Привет.\n\n"
        "→ Добавляй задачи\n"
        "→ Следи за списком\n"
        "→ Закрывай выполненное\n"
    )

    await smart_send(msg, text, get_main_kb(user_id))


# ДОБАВИТЬ
@dp.message(lambda m: m.text == "＋ Добавить")
async def add_task(msg: types.Message):
    update_user(msg.from_user.id)
    user_state[msg.from_user.id] = "adding"
    await smart_send(msg, "→ Напиши задачу")

@dp.message(lambda m: user_state.get(m.from_user.id) == "adding")
async def save_task(msg: types.Message):
    user_id = msg.from_user.id
    update_user(user_id)

    user_tasks.setdefault(user_id, []).append({
        "text": msg.text,
        "done": False
    })

    user_state[user_id] = None
    await smart_send(msg, "✓ Добавлено", get_main_kb(user_id))


# СПИСОК
@dp.message(lambda m: m.text == "≡ Список")
async def list_tasks(msg: types.Message):
    user_id = msg.from_user.id
    update_user(user_id)

    tasks = user_tasks.get(user_id, [])

    if not tasks:
        await smart_send(msg, "→ Пусто", get_main_kb(user_id))
        return

    text = "≡ <b>Твои задачи:</b>\n\n"

    for i, t in enumerate(tasks):
        status = "✓" if t["done"] else "×"
        text += f"{i+1}. {t['text']} [{status}]\n"

    text += "\n<i>Введи номер</i>"

    user_state[user_id] = "choosing"
    await smart_send(msg, text)


# ACTION (важно выше choosing)
@dp.message(lambda m: user_state.get(m.from_user.id, "").startswith("action_"))
async def task_action(msg: types.Message):
    user_id = msg.from_user.id
    update_user(user_id)

    tasks = user_tasks.get(user_id, [])
    index = int(user_state[user_id].split("_")[1])

    if msg.text == "✓ Готово":
        tasks[index]["done"] = True
        await smart_send(msg, "✓ Выполнено", get_main_kb(user_id))

    elif msg.text == "× Удалить":
        tasks.pop(index)
        await smart_send(msg, "× Удалено", get_main_kb(user_id))

    elif msg.text == "← Назад":
        user_state[user_id] = None
        await smart_send(msg, "← Назад", get_main_kb(user_id))
        return

    else:
        await smart_send(msg, "→ Используй кнопки", action_kb)
        return

    user_state[user_id] = None


# ВЫБОР
@dp.message(lambda m: user_state.get(m.from_user.id) == "choosing" and m.text.isdigit())
async def choose_task(msg: types.Message):
    user_id = msg.from_user.id
    update_user(user_id)

    tasks = user_tasks.get(user_id, [])
    index = int(msg.text) - 1

    if index < 0 or index >= len(tasks):
        await smart_send(msg, "→ Нет такой задачи")
        return

    user_state[user_id] = f"action_{index}"

    text = f"→ <b>{tasks[index]['text']}</b>\n\nВыбери действие"
    await smart_send(msg, text, action_kb)


# АДМИНКА
@dp.message(lambda m: m.text == "⚙ Админ" and m.from_user.id == ADMIN_ID)
async def admin_panel(msg: types.Message):
    update_user(msg.from_user.id)
    user_state[msg.from_user.id] = "admin"
    await smart_send(msg, "⚙ Админ панель", admin_kb)


# РАССЫЛКА
@dp.message(lambda m: m.text == "📢 Рассылка" and m.from_user.id == ADMIN_ID)
async def mailing_start(msg: types.Message):
    user_state[msg.from_user.id] = "mailing"
    await smart_send(msg, "→ Отправь текст или фото")

@dp.message(lambda m: user_state.get(m.from_user.id) == "mailing")
async def mailing_send(msg: types.Message):
    sent = 0

    for uid in users_db.keys():
        try:
            if msg.photo:
                await bot.send_photo(uid, msg.photo[-1].file_id, caption=msg.caption or "")
            else:
                await bot.send_message(uid, msg.text)
            sent += 1
        except:
            pass

    user_state[msg.from_user.id] = None
    await smart_send(msg, f"✓ Отправлено: {sent}", admin_kb)


# СПИСОК ЮЗЕРОВ
@dp.message(lambda m: m.text == "👥 Пользователи" and m.from_user.id == ADMIN_ID)
async def users_list(msg: types.Message):
    text = "👥 Пользователи:\n\n"

    for uid, last in users_db.items():
        dt = time.strftime("%d.%m %H:%M", time.localtime(last))
        text += f"{uid} → {dt}\n"

    await smart_send(msg, text, admin_kb)


# НАЗАД
@dp.message(lambda m: m.text == "← Назад")
async def back(msg: types.Message):
    user_state[msg.from_user.id] = None
    await start(msg)


# ЛОГ АКТИВНОСТИ
@dp.message()
async def track(msg: types.Message):
    update_user(msg.from_user.id)


# СТАРТ
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
