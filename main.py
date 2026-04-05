import asyncio
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.session.aiohttp import AiohttpSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import database as db

load_dotenv()
db.init_db()

TOKEN = os.getenv("BOT_TOKEN")

# --- НАСТРОЙКА ПРОКСИ (ВАЖНО ДЛЯ PYTHONANYWHERE) ---
if os.environ.get('PYTHONANYWHERE_DOMAIN'):
    session = AiohttpSession(proxy="http://proxy.server:3128")
    bot = Bot(token=TOKEN, session=session)
else:
    bot = Bot(token=TOKEN)
# ---------------------------------------------------

dp = Dispatcher()
scheduler = AsyncIOScheduler()


async def send_reminder(chat_id, text):
    await bot.send_message(chat_id, f"⏰ **НАПОМИНАНИЕ!**\n\nПора делать: {text}")


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db.add_user_if_not_exists(message.from_user.id)
    await message.answer("Привет! Я Study Bot. 👋\nПиши: `Задача | 15:30` для напоминания.")


@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    tasks = db.get_tasks(message.from_user.id)
    if not tasks:
        await message.answer("Задач нет!")
        return
    for t_id, text in tasks:
        kb = InlineKeyboardBuilder()
        kb.add(types.InlineKeyboardButton(text="✅ Готово", callback_data=f"done_{t_id}"))
        await message.answer(f"📌 {text}", reply_markup=kb.as_markup())


@dp.message(F.text)
async def handle_text(message: types.Message):
    if message.text.startswith('/'): return

    text = message.text
    if "|" in text:
        parts = text.split("|")
        task_text = parts[0].strip()
        try:
            target = datetime.strptime(parts[1].strip(), "%H:%M").replace(
                year=datetime.now().year, month=datetime.now().month, day=datetime.now().day
            )
            scheduler.add_job(send_reminder, "date", run_date=target, args=[message.chat.id, task_text])
            text = task_text
            await message.answer(f"🔔 Напомню в {parts[1].strip()}")
        except:
            await message.answer("❌ Ошибка времени. Формат: 18:30")
            return

    db.add_user_if_not_exists(message.from_user.id)
    db.add_task(message.from_user.id, text)
    await message.answer(f"✅ Добавлено: {text}")


@dp.callback_query(F.data.startswith("done_"))
async def task_done(call: types.CallbackQuery):
    t_id = int(call.data.split("_")[1])
    db.delete_task(t_id)
    xp = db.update_xp(call.from_user.id, 10)
    await call.message.edit_text(f"🌟 Выполнено! Опыт: {xp}")


async def main():
    scheduler.start()
    print("Бот запущен через прокси!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())