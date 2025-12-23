import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from langchain_gigachat.chat_models import GigaChat

# --- КОНФИГУРАЦИЯ ---
TOKEN = "7981362710:AAE8yFG-pgP_MPrrvhw7ayF-CLLQBK2Sw4g"
ADMIN_ID = 1150861829
# Твой ключ авторизации GigaChat
GIGA_AUTH_KEY = "MDE5YjQ4Y2MtYzdkYy03YmJiLWFkNDctMzNmZmFiYjRkYWQ5OjYxM2QwNWNhLWRkNmItNDk4Ni05MDU4LTY2MTYyMDI4MzQzZg=="

# Настройка ИИ GigaChat
llm = GigaChat(
    credentials=GIGA_AUTH_KEY,
    verify_ssl_certs=False, # Важно для работы на некоторых серверах
    model="GigaChat"
)

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
        await message.answer(f"Привет, босс! Ссылка: https://t.me/{bot_user.username}")
    else:
        await message.answer("Выбери режим работы:", reply_markup=get_main_kb())

@dp.message(F.text == "🤖 Помощь ИИ (задачки)")
async def set_ai_mode(message: types.Message, state: FSMContext):
    await state.set_state(UserState.is_ai_mode)
    await message.answer("🤖 Режим GigaChat включен. Присылай задачу или вопрос!")

@dp.message(F.text == "👤 Написать владельцу")
async def set_owner_mode(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("👤 Режим анонимки включен. Что передать владельцу?")

@dp.message(F.text)
async def handle_messages(message: types.Message, state: FSMContext):
    # Ответы админа (владельца)
    if message.from_user.id == ADMIN_ID and message.reply_to_message:
        try:
            target_id = int(message.reply_to_message.text.split("#id")[-1])
            await bot.send_message(target_id, f"✉️ **Ответ от владельца:**\n\n{message.text}")
            await message.answer("✅ Отправлено!")
        except:
            await message.answer("❌ Нужно нажать 'ответить' на сообщение с тегом #id.")
        return

    # Режим работы для пользователя
    current_state = await state.get_state()
    
    if current_state == UserState.is_ai_mode:
        waiting_msg = await message.answer("⏳ *GigaChat думает...*", parse_mode="Markdown")
        try:
            # Запрос к GigaChat
            response = llm.invoke(message.text)
            await waiting_msg.edit_text(f"🤖 **Ответ ИИ:**\n\n{response.content}")
        except Exception as e:
            await waiting_msg.edit_text(f"❌ Ошибка ИИ: Не удалось получить ответ. Проверь статус ключа в кабинете Сбера.")
            print(f"GigaChat Error: {e}")
    
    else:
        # Анонимное сообщение владельцу
        if message.from_user.id != ADMIN_ID:
            await bot.send_message(
                ADMIN_ID, 
                f"📩 **Новый вопрос:**\n\n{message.text}\n\n#id{message.from_user.id}"
            )
            await message.answer("🚀 Твое сообщение отправлено!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
