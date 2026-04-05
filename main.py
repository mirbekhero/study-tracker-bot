import asyncio
import os
from datetime import datetime
import pytz
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
bishkek_tz = pytz.timezone('Asia/Bishkek')
if os.environ.get('PYTHONANYWHERE_DOMAIN'):
    session = AiohttpSession(proxy="http://proxy.server:3128")
    bot = Bot(token=TOKEN, session=session)
else:
    bot = Bot(token=TOKEN)

dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=bishkek_tz)
async def send_reminder(chat_id, text):
    try:
        await bot.send_message(chat_id, f"⏰ **ВРЕМЯ ВЫШЛО!**\n\nНужно сделать: {text}")
    except Exception as e:
        print(f"Ошибка при отправке уведомления: {e}")


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db.add_user_if_not_exists(message.from_user.id)
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я твой Study Bot. Вот как со мной работать:\n"
        "1. Просто напиши задачу, чтобы добавить её в список.\n"
        "2. Напиши `Задача | ЧЧ:ММ`, чтобы я напомнил о ней (например: `Матан | 19:00`).\n"
        "3. Используй /list, чтобы увидеть свои дела."
    )


@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    tasks = db.get_tasks(message.from_user.id)
    if not tasks:
        await message.answer("Твой список пуст. Отдыхай! ☕️")
        return

    await message.answer("📌 Твои текущие задачи:")
    for task_id, text in tasks:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(
            text="✅ Готово (+10 XP)",
            callback_data=f"done_{task_id}")
        )
        await message.answer(f"• {text}", reply_markup=builder.as_markup())


@dp.message(F.text)
async def handle_text(message: types.Message):
    if message.text.startswith('/'): return

    user_input = message.text
    task_text = user_input
    reminder_info = ""


    if "|" in user_input:
        parts = user_input.split("|")
        task_text = parts[0].strip()
        time_str = parts[1].strip()

        try:
            now = datetime.now(bishkek_tz)

            time_obj = datetime.strptime(time_str, "%H:%M")


            target_time = bishkek_tz.localize(datetime(
                year=now.year, month=now.month, day=now.day,
                hour=time_obj.hour, minute=time_obj.minute
            ))
            if target_time < now:
                await message.answer("❌ Это время уже прошло! Введи время в будущем.")
                return
            scheduler.add_job(
                send_reminder,
                "date",
                run_date=target_time,
                args=[message.chat.id, task_text]
            )
            reminder_info = f"\n⏰ Напомню в {time_str} (по Бишкеку)"

        except ValueError:
            await message.answer("❌ Неверный формат времени! Пиши так: `Задача | 15:30`")
            return

    db.add_user_if_not_exists(message.from_user.id)
    db.add_task(message.from_user.id, task_text)

    await message.answer(f"📥 Задача добавлена: {task_text}{reminder_info}")


@dp.callback_query(F.data.startswith("done_"))
async def task_done(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    db.delete_task(task_id)
    new_xp = db.update_xp(callback.from_user.id, 10)

    await callback.message.edit_text(
        f"🌟 Отлично! Задача выполнена.\nТвой опыт: {new_xp} XP"
    )
    await callback.answer()


async def main():
    # Запускаем планировщик перед опросом бота
    scheduler.start()
    print("Бот запущен! Часовой пояс: Asia/Bishkek")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")