import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
import database as db

load_dotenv()
db.init_db()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()
def get_rank(xp):
    if xp < 50: return "🫥 Амеба"
    if xp < 150: return "🐣 Первокурсник"
    if xp < 300: return "🦾 Бывалый Студент"
    return "🧙‍♂️ Магистр Дедлайнов"
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db.add_user_if_not_exists(message.from_user.id)
    await message.answer("Твой Study Bot с вечной памятью готов! \nНапиши задачу или нажми /list")
@dp.message(Command("list"))
async def cmd_list(message: types.Message):
    tasks = db.get_tasks(message.from_user.id)
    if not tasks:
        await message.answer("Задач нет. Отдыхай!")
        return
    for task_id, text in tasks:
        builder = InlineKeyboardBuilder()
        builder.add(types.InlineKeyboardButton(text="✅ Готово", callback_data=f"done_{task_id}"))
        await message.answer(f"📌 {text}", reply_markup=builder.as_markup())
@dp.message(F.text)
async def handle_text(message: types.Message):
    db.add_user_if_not_exists(message.from_user.id)
    db.add_task(message.from_user.id, message.text)
    await message.answer(f"Записал: {message.text}")
@dp.callback_query(F.data.startswith("done_"))
async def task_done(callback: types.CallbackQuery):
    task_id = int(callback.data.split("_")[1])
    db.delete_task(task_id)
    new_xp = db.update_xp(callback.from_user.id, 10)
    await callback.message.edit_text(f"✅ Выполнено! Твой опыт: {new_xp} XP ({get_rank(new_xp)})")
    await callback.answer()
async def main():
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())