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

# Настройка ИИ с использованием REST-транспорта для обхода блокировок
try:
    genai.configure(api_key=AI_API_KEY, transport='rest')
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    print(f"Ошибка инициализации Gemini: {e}")

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
        await message.answer(f"Привет, босс! Твоя ссылка: https://t.me/{bot_user.username}\nБот готов к работе.")
    else:
        await message.answer("Привет! Выбери режим:", reply_markup=get_main_kb())

@dp.message(F.text == "🤖 Помощь ИИ (задачки)")
async def set_ai_mode(message: types.Message, state: FSMContext):
    await state.set_state(UserState.is_ai_mode)
    await message.answer("🤖 Режим ИИ включен. Присылай задачу!")

@dp.message(F.text == "👤 Написать владельцу")
async def set_owner_mode(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("👤 Режим анонимки включен. Напиши сообщение.")

@dp.message(F.text)
async def handle_messages(message: types.Message, state: FSMContext):
    # Ответы владельца
    if message.from_user.id == ADMIN_ID and message.reply_to_message:
        try:
            target_id = int(message.reply_to_message.text.split("#id")[-1])
            await bot.send_message(target_id, f"✉️ **Ответ от владельца:**\n\n{message.text}")
            await message.answer("✅ Отправлено!")
        except:
            await message.answer("❌ Ошибка: нужно отвечать на сообщение с #id.")
        return

    # Логика для пользователя
    current_state = await state.get_state()
    
    if current_state == UserState.is_ai_mode:
        waiting_msg = await message.answer("⏳ *ИИ анализирует...*", parse_mode="Markdown")
        try:
            # Запрос к нейросети
            response = model.generate_content(message.text)
            
            if response and response.text:
                await waiting_msg.edit_text(f"🤖 **Ответ ИИ:**\n\n{response.text}")
            else:
                await waiting_msg.edit_text("⚠️ ИИ не выдал текст. Попробуй переформулировать.")
        
        except Exception as e:
            error_str = str(e)
            print(f"ERROR: {error_str}")
            # Если даже REST не помог, выводим подсказку
            if "location" in error_str.lower() or "403" in error_str:
                await waiting_msg.edit_text("❌ Ошибка: Google блокирует этот сервер по региону. Попробуй другой вопрос или напиши владельцу.")
            else:
                await waiting_msg.edit_text(f"❌ Ошибка ИИ: {error_str[:100]}")
    
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
