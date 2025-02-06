import logging
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import json
import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Белый список для пользователей
WHITELIST = []

# API ключ 
IMEI_API_KEY = "e4oEaZY1Kom5OXzybETkMlwjOCy3i8GSCGTHzWrhd4dc563b"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    user_id = update.effective_user.id
    if user_id in WHITELIST:
        await update.message.reply_text(
            "Добро пожаловать! Вы авторизованы. Пожалуйста, отправьте IMEI вашего устройства (15 цифр)."
        )
    else:
        await update.message.reply_text(
            "Извините, вы не авторизованы для использования данного бота."
        )

def validate_imei(imei: str) -> bool:
    """
    Валидируем
    """
    return bool(re.fullmatch(r"\d{15}", imei))

async def process_imei(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    user_id = update.effective_user.id
    
    if user_id not in WHITELIST:
        await update.message.reply_text(
            "Извините, вы не авторизованы для использования данного бота. "
            
        )
        return

    imei = update.message.text.strip()
    if not validate_imei(imei):
        await update.message.reply_text(
            "Неверный формат IMEI. Убедитесь, что вы вводите 15 цифр."
        )
        return

    # URL API проверки IMEI
    api_url = "https://api.imeicheck.net/v1/checks"

    # Заголовки запроса
    headers = {
        "Authorization": f"Bearer {IMEI_API_KEY}",
        "Accept-Language": "en",
        "Content-Type": "application/json"
    }

    # Тело запроса
    payload = {
        "deviceId": imei,
        "serviceId": 12
    }

    try:
        
        payload_json = json.dumps(payload)
        response = requests.post(api_url, data=payload_json, headers=headers, timeout=10)
        
        response.raise_for_status()
        data = response.json()
        properties = data.get("properties", {})

        
        
        purchase_date = properties.get("estPurchaseDate")
        if purchase_date:
            purchase_date = datetime.datetime.utcfromtimestamp(purchase_date).strftime('%Y-%m-%d')
        else:
            purchase_date = "Неизвестно"

        message_text = (
            f"📱 *Информация об устройстве* 📱\n\n"
            f"🔹 *Название устройства:* {properties.get('deviceName', 'Неизвестно')}\n"
            f"🔹 *IMEI:* {properties.get('imei', 'Неизвестно')}\n"
            f"🔹 *MEID:* {properties.get('meid', 'Неизвестно')}\n"
            f"🔹 *IMEI2:* {properties.get('imei2', 'Не указано')}\n"
            f"🔹 *Серийный номер:* {properties.get('serial', 'Неизвестно')}\n"
            f"🔹 *Дата покупки:* {purchase_date}\n"
            f"🔹 *Блокировка SIM-карты:* {'✅ Да' if properties.get('simLock') else '❌ Нет'}\n"
            f"🔹 *Техническая поддержка:* {'✅ Да' if properties.get('technicalSupport') else '❌ Нет'}\n"
            f"🔹 *Демо-устройство:* {'✅ Да' if properties.get('demoUnit') else '❌ Нет'}\n"
            f"🔹 *Восстановленный (Refurbished):* {'✅ Да' if properties.get('refurbished') else '❌ Нет'}\n"
            f"🔹 *Страна покупки:* {properties.get('purchaseCountry', 'Неизвестно')}\n"
            f"🔹 *Модель Apple:* {properties.get('apple/modelName', 'Неизвестно')}\n"
            f"🔹 *Статус блокировки в США:* 🚨 {properties.get('usaBlockStatus', 'Неизвестно')}\n"
            f"🔹 *Сеть:* 🌍 {properties.get('network', 'Неизвестно')}\n"
        )

    
        await update.message.reply_text(message_text, parse_mode="Markdown")

        
        image_url = properties.get("image")
        if image_url:
            await update.message.reply_photo(photo=image_url)
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к API: {e}")
        await update.message.reply_text("Ошибка при соединении с сервером. Попробуйте позже.")
    except ValueError:
        await update.message.reply_text("Ошибка при обработке ответа от сервера.")

def main() -> None:
    
    # Токен  Telegram-бота
    TOKEN = ""

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_imei))

    application.run_polling()

if __name__ == '__main__':
    main()