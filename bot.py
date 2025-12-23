import asyncio
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# --- КОНФИГУРАЦИЯ ---
TOKEN = "7981362710:AAE8yFG-pgP_MPrrvhw7ayF-CLLQBK2Sw4g"
ADMIN_ID = 1150861829
AI_API_KEY = "AIzaSyDSxDkw6deZjjbT1WU-T6pWw9atfk3567s"

# Настройка нейросети
genai.configure(api_key=AI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # Быстрая и точная модель

bot = Bot(token=TOKEN)
dp = Dispatcher()


class UserState(StatesGroup):
    is_ai_mode = State()


def get_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.button(text="👤 Написать владельцу")
    builder.button(text="🤖 Помощь ИИ (задачки)")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


@dp.message(CommandStart())
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user.id == ADMIN_ID:
        bot_user = await bot.get_me()
        await message.answer(f"Привет, босс! Твоя ссылка: https://t.me/{bot_user.username}\n\n"
                             f"Тут будут анонимные вопросы.")
    else:
        await message.answer(
            "Привет! Я могу передать твой вопрос владельцу анонимно или помочь решить задачу с помощью ИИ. Выбери режим:",
            reply_markup=get_main_kb())


@dp.message(F.text == "🤖 Помощь ИИ (задачки)")
async def set_ai_mode(message: types.Message, state: FSMContext):
    await state.set_state(UserState.is_ai_mode)
    await message.answer("🤖 Режим ИИ включен. Присылай условие задачи или любой вопрос — я постараюсь помочь!")


@dp.message(F.text == "👤 Написать владельцу")
async def set_owner_mode(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("👤 Режим анонимности включен. Напиши что-нибудь, и я передам это владельцу.")


@dp.message(F.text)
async def handle_messages(message: types.Message, state: FSMContext):
    # Логика ответов админа
    if message.from_user.id == ADMIN_ID and message.reply_to_message:
        try:
            target_id = int(message.reply_to_message.text.split("#id")[-1])
            await bot.send_message(target_id, f"✉️ **Ответ от владельца:**\n\n{message.text}")
            await message.answer("✅ Отправлено!")
        except:
            await message.answer("❌ Ошибка: нужно отвечать на сообщение с #id.")
        return

    # Логика пользователя
    current_state = await state.get_state()

    if current_state == UserState.is_ai_mode:
        waiting_msg = await message.answer("⏳ *ИИ анализирует ваш запрос...*", parse_mode="Markdown")
        try:
            # Запрос к нейросети
            response = model.generate_content(f"Реши задачу или ответь на вопрос кратко и понятно: {message.text}")
            await waiting_msg.edit_text(f"🤖 **Ответ ИИ:**\n\n{response.text}", parse_mode="Markdown")
        except Exception as e:
            await waiting_msg.edit_text("❌ Произошла ошибка при обращении к ИИ. Попробуйте позже.")

    else:
        if message.from_user.id != ADMIN_ID:
            await bot.send_message(
                ADMIN_ID,
                f"📩 **Анонимный вопрос:**\n\n{message.text}\n\n#id{message.from_user.id}"
            )
            await message.answer("🚀 Сообщение отправлено! Если владелец ответит, ты получишь уведомление.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
