Марк Юсупов, [05.11.2025 21:14]
import asyncio
import logging
import os
import aiosqlite
import sys
import atexit

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# 🔹 Токен берём из переменной окружения
API_TOKEN = os.getenv("7416758978:AAESVhBiVM9uKW6QfD0h-_DyEgMeR5UsRMs")
ADMIN_ID = int(os.getenv("808414789","0"))
import asyncio
import logging
import os
import aiosqlite
import sys
import atexit

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# 🔹 Токен берём из переменной окружения
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not API_TOKEN:
    print("❌ Ошибка: не задан API_TOKEN")
    sys.exit(1)

# 🔹 Проверка, чтобы не запустить второй процесс
LOCKFILE = "bot.lock"
if os.path.exists(LOCKFILE):
    print("⚠️ Бот уже запущен. Выход.")
    sys.exit()
with open(LOCKFILE, "w") as f:
    f.write(str(os.getpid()))
@atexit.register
def remove_lock():
    if os.path.exists(LOCKFILE):
        os.remove(LOCKFILE)

# 🔹 Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔹 Инициализация
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# 🔹 FSM для добавления кнопок
class ButtonFSM(StatesGroup):
    waiting_for_text = State()
    waiting_for_url = State()

DB_FILE = "bot.db"


# =============== DATABASE ==================
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS buttons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            url TEXT NOT NULL
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS required_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL
        )
        """)
        await db.commit()


async def get_buttons():
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT text, url FROM buttons") as cursor:
            rows = await cursor.fetchall()
            return [InlineKeyboardButton(text=r[0], url=r[1]) for r in rows]


async def get_channels():
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT username FROM required_channels") as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]


async def check_subscription(user_id: int) -> bool:
    channels = await get_channels()
    if not channels:
        return True
    for channel in channels:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True


# =============== ADMIN COMMANDS ==================
@dp.message(Command("add_button"))
async def add_button(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Введите текст кнопки:")
    await state.set_state(ButtonFSM.waiting_for_text)

@dp.message(ButtonFSM.waiting_for_text)
async def button_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("Теперь отправьте ссылку (URL):")
    await state.set_state(ButtonFSM.waiting_for_url)

@dp.message(ButtonFSM.waiting_for_url)
async def button_url(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("INSERT INTO buttons (text, url) VALUES (?, ?)", (data["text"], message.text))
        await db.commit()
    await message.answer("✅ Кнопка добавлена.")
    await state.clear()

@dp.message(Command("list_buttons"))
async def list_buttons(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT id, text, url FROM buttons") as cursor:
            rows = await cursor.fetchall()
            if not rows:
                return await message.answer("Нет кнопок.")

Марк Юсупов, [05.11.2025 21:14]
text = "\n".join([f"{r[0]}. {r[1]} — {r[2]}" for r in rows])
            await message.answer(text)

@dp.message(Command("remove_button"))
async def remove_button(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.answer("Использование: /remove_button <id>")
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM buttons WHERE id = ?", (int(parts[1]),))
        await db.commit()
    await message.answer("✅ Кнопка удалена.")


# === CHANNEL COMMANDS ===
@dp.message(Command("add_channel"))
async def add_channel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].startswith("@"):
        return await message.answer("Использование: /add_channel @username")
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("INSERT INTO required_channels (username) VALUES (?)", (parts[1],))
        await db.commit()
    await message.answer("✅ Канал добавлен.")

@dp.message(Command("list_channels"))
async def list_channels(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    channels = await get_channels()
    if not channels:
        return await message.answer("Список каналов пуст.")
    await message.answer("\n".join(channels))

@dp.message(Command("remove_channel"))
async def remove_channel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].startswith("@"):
        return await message.answer("Использование: /remove_channel @username")
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM required_channels WHERE username = ?", (parts[1],))
        await db.commit()
    await message.answer("✅ Канал удалён.")


# =============== MESSAGE HANDLER ==================
@dp.message()
async def handle_message(message: Message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    chat_id = message.chat.id

    if await check_subscription(user_id):
        return

    await message.delete()
    buttons = await get_buttons()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[b] for b in buttons]) if buttons else None
    msg = await bot.send_message(
        chat_id=chat_id,
        text=f"{message.from_user.mention_html()}, подпишитесь на все каналы, чтобы писать в чат.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await asyncio.sleep(30)
    try:
        await bot.delete_message(chat_id, msg.message_id)
    except:
        pass


# =============== MAIN ==================
async def main():
    await init_db()
    await dp.start_polling(bot)

if name == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")

Марк Юсупов, [05.11.2025 21:25]
808414789", "0"))

if not API_TOKEN:
    print("❌ Ошибка: не задан API_TOKEN")
    sys.exit(1)

# 🔹 Проверка, чтобы не запустить второй процесс
LOCKFILE = "bot.lock"
if os.path.exists(LOCKFILE):
    print("⚠️ Бот уже запущен. Выход.")
    sys.exit()
with open(LOCKFILE, "w") as f:
    f.write(str(os.getpid()))
@atexit.register
def remove_lock():
    if os.path.exists(LOCKFILE):
        os.remove(LOCKFILE)

# 🔹 Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔹 Инициализация
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# 🔹 FSM для добавления кнопок
class ButtonFSM(StatesGroup):
    waiting_for_text = State()
    waiting_for_url = State()

DB_FILE = "bot.db"


# =============== DATABASE ==================
async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS buttons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            url TEXT NOT NULL
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS required_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL
        )
        """)
        await db.commit()


async def get_buttons():
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT text, url FROM buttons") as cursor:
            rows = await cursor.fetchall()
            return [InlineKeyboardButton(text=r[0], url=r[1]) for r in rows]


async def get_channels():
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT username FROM required_channels") as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]


async def check_subscription(user_id: int) -> bool:
    channels = await get_channels()
    if not channels:
        return True
    for channel in channels:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True


# =============== ADMIN COMMANDS ==================
@dp.message(Command("add_button"))
async def add_button(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Введите текст кнопки:")
    await state.set_state(ButtonFSM.waiting_for_text)

@dp.message(ButtonFSM.waiting_for_text)
async def button_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("Теперь отправьте ссылку (URL):")
    await state.set_state(ButtonFSM.waiting_for_url)

@dp.message(ButtonFSM.waiting_for_url)
async def button_url(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    data = await state.get_data()
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("INSERT INTO buttons (text, url) VALUES (?, ?)", (data["text"], message.text))
        await db.commit()
    await message.answer("✅ Кнопка добавлена.")
    await state.clear()

@dp.message(Command("list_buttons"))
async def list_buttons(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT id, text, url FROM buttons") as cursor:
            rows = await cursor.fetchall()
            if not rows:
                return await message.answer("Нет кнопок.")

Марк Юсупов, [05.11.2025 21:14]
text = "\n".join([f"{r[0]}. {r[1]} — {r[2]}" for r in rows])
            await message.answer(text)

@dp.message(Command("remove_button"))
async def remove_button(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.answer("Использование: /remove_button <id>")
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM buttons WHERE id = ?", (int(parts[1]),))
        await db.commit()
    await message.answer("✅ Кнопка удалена.")


# === CHANNEL COMMANDS ===
@dp.message(Command("add_channel"))
async def add_channel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].startswith("@"):
        return await message.answer("Использование: /add_channel @username")
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("INSERT INTO required_channels (username) VALUES (?)", (parts[1],))
        await db.commit()
    await message.answer("✅ Канал добавлен.")

@dp.message(Command("list_channels"))
async def list_channels(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    channels = await get_channels()
    if not channels:
        return await message.answer("Список каналов пуст.")
    await message.answer("\n".join(channels))

@dp.message(Command("remove_channel"))
async def remove_channel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].startswith("@"):
        return await message.answer("Использование: /remove_channel @username")
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("DELETE FROM required_channels WHERE username = ?", (parts[1],))
        await db.commit()
    await message.answer("✅ Канал удалён.")


# =============== MESSAGE HANDLER ==================
@dp.message()
async def handle_message(message: Message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    chat_id = message.chat.id

    if await check_subscription(user_id):
        return

    await message.delete()
    buttons = await get_buttons()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[b] for b in buttons]) if buttons else None
    msg = await bot.send_message(
        chat_id=chat_id,
        text=f"{message.from_user.mention_html()}, подпишитесь на все каналы, чтобы писать в чат.",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await asyncio.sleep(30)
    try:
        await bot.delete_message(chat_id, msg.message_id)
    except:
        pass


# =============== MAIN ==================
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")
