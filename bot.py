import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart

# Твои данные уже вставлены
TOKEN = "7981362710:AAE8yFG-pgP_MPrrvhw7ayF-CLLQBK2Sw4g"
ADMIN_ID = 1150861829

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        bot_info = await bot.get_me()
        link = f"https://t.me/{bot_info.username}"
        await message.answer(f"Привет! Это твой бот для вопросов.\n\n"
                             f"Твоя ссылка: {link}\n\n"
                             f"Чтобы ответить человеку, нажми 'Ответить' на его вопрос.")
    else:
        await message.answer("Привет! Напиши сюда любой вопрос, и я передам его владельцу анонимно. 💬")


@dp.message(F.text)
async def handle_messages(message: types.Message):
    # Если пишет НЕ админ (анонимный пользователь)
    if message.from_user.id != ADMIN_ID:
        # Отправляем сообщение тебе, добавляя в конец ID пользователя
        # Мы используем невидимый символ или просто текст, чтобы бот знал, кому отвечать
        await bot.send_message(
            ADMIN_ID,
            f"📩 **Новый вопрос:**\n\n{message.text}\n\n"
            f"——\nID: #id{message.from_user.id}",
            parse_mode="Markdown"
        )
        await message.answer("Отправлено! Автор скоро прочтет твое сообщение. 😉")

    # Если пишет админ И это ответ (Reply) на сообщение бота
    elif message.from_user.id == ADMIN_ID and message.reply_to_message:
        try:
            # Вытаскиваем ID из текста сообщения, на которое отвечаем
            reply_text = message.reply_to_message.text
            if "#id" in reply_text:
                target_id = int(reply_text.split("#id")[-1])

                # Отправляем ответ пользователю
                await bot.send_message(target_id, f"✉️ **Тебе пришел ответ:**\n\n{message.text}", parse_mode="Markdown")
                await message.answer("✅ Твой ответ отправлен!")
            else:
                await message.answer("❌ Ошибка: не удалось найти ID пользователя в этом сообщении.")
        except Exception as e:
            await message.answer(f"❌ Ошибка при отправке: {e}")

    # Если админ пишет просто так
    else:
        await message.answer("Чтобы ответить на вопрос, используй функцию 'Ответить' (Reply).")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())