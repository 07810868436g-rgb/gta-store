import asyncio
import json
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, WebAppInfo, LabeledPrice, CallbackQuery, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.exc import IntegrityError

# Импорты нашей базы данных
from database.engine import async_session, init_models
from database.models import GameKey, KeyStatus

# Загружаем секреты из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("КРИТИЧЕСКАЯ ОШИБКА: Токен бота не найден. Проверьте файл .env!")

WEBAPP_URL = "https://example.com" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ---------------------------------------------------------
# Обработчик команды /start
# ---------------------------------------------------------
@dp.message(CommandStart())
async def start_cmd(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🎮 Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))
    
    await message.answer(
        "Добро пожаловать в элитный магазин цифровых товаров.\nНажми на кнопку ниже, чтобы открыть витрину 👇",
        reply_markup=builder.as_markup()
    )

# ---------------------------------------------------------
# Обработчик данных из Mini App (нажатие кнопки "Купить")
# ---------------------------------------------------------
@dp.message(F.web_app_data)
async def web_app_data_handler(message: Message):
    data = json.loads(message.web_app_data.data)
    
    if data.get("action") == "buy_key" and data.get("item") == "gta6_ru":
        price_rub = data.get("price")
        
        # Создаем меню выбора способа оплаты
        builder = InlineKeyboardBuilder()
        
        # 1. Основной шлюз для РФ (заглушка для ссылки на оплату)
        builder.row(InlineKeyboardButton(
            text="💳 Оплатить Картой / СБП", 
            url="https://pay.lava.ru/invoice/dummy_link"
        ))
        
        # 2. Оплата криптой
        builder.row(InlineKeyboardButton(
            text="🪙 Оплатить Криптовалютой", 
            url="https://t.me/CryptoBot?start=dummy_link"
        ))
        
        # 3. Альтернатива: Telegram Stars (вызовет отдельную функцию)
        builder.row(InlineKeyboardButton(
            text="⭐️ Оплатить Звездами (TG)", 
            callback_data="pay_stars_gta6"
        ))
        
        await message.answer(
            f"🛒 **Оформление заказа**\n\n"
            f"Товар: Ключ GTA 6 (PC/RU)\n"
            f"К оплате: **{price_rub} руб.**\n\n"
            f"Выберите удобный способ оплаты:",
            parse_mode="Markdown",
            reply_markup=builder.as_markup()
        )

# ---------------------------------------------------------
# Обработчик для дополнительного метода (Telegram Stars)
# ---------------------------------------------------------
@dp.callback_query(F.data == "pay_stars_gta6")
async def process_stars_payment(callback: CallbackQuery):
    await callback.answer() # Убираем часики на кнопке
    
    prices = [LabeledPrice(label="Ключ GTA 6 (PC/RU)", amount=2500)]
    
    await callback.message.answer_invoice(
        title="Grand Theft Auto VI",
        description="Оплата через внутреннюю валюту Telegram.",
        payload="invoice_gta6_payload",
        provider_token="",              
        currency="XTR",                 
        prices=prices,
        is_flexible=False               
    )

# ---------------------------------------------------------
# Скрытая Админка: Загрузка ключей
# ---------------------------------------------------------
@dp.message(F.document)
async def admin_key_upload(message: Message, bot: Bot):
    # 1. Проверяем, что это админ
    admin_id = int(os.getenv("ADMIN_ID", 0))
    if message.from_user.id != admin_id:
        return # Если пишет не админ, бот просто игнорирует файл
        
    # 2. Проверяем, что это текстовый файл
    if not message.document.file_name.endswith('.txt'):
        return await message.answer("⚠️ Ошибка: Пожалуйста, загрузите ключи в формате .txt")
    
    msg = await message.answer("⏳ Скачиваю и проверяю ключи...")
    
    # 3. Скачиваем файл в оперативную память
    file = await bot.download(message.document)
    content = file.read().decode('utf-8')
    
    # 4. Разбиваем на строки и убираем пустые
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    
    if not lines:
        return await msg.edit_text("⚠️ Ошибка: Файл пуст.")
        
    # 5. Записываем в базу данных
    added = 0
    duplicates = 0
    
    async with async_session() as session:
        for key_val in lines:
            new_key = GameKey(
                item_slug="gta6_ru", # Привязываем к нашему товару
                key_value=key_val,
                status=KeyStatus.AVAILABLE
            )
            session.add(new_key)
            
            try:
                # Пытаемся сохранить каждый ключ. Если такой уже есть - перехватываем ошибку
                await session.commit()
                added += 1
            except IntegrityError:
                await session.rollback()
                duplicates += 1
                
    # 6. Отчитываемся о результате
    report = f"✅ **Загрузка завершена!**\n\nУспешно добавлено: {added} шт."
    if duplicates > 0:
        report += f"\nПропущено дубликатов: {duplicates} шт."
        
    await msg.edit_text(report, parse_mode="Markdown")

# ---------------------------------------------------------
# Запуск бота
# ---------------------------------------------------------
async def main():
    print("Инициализация базы данных...")
    await init_models() # <- Вот тут бот сам создаст таблицы при запуске
    
    print("Бот успешно запущен. Ожидание запросов...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())