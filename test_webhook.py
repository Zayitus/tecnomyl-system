# test_webhook.py
import asyncio
from telegram import Bot

# Configura el token de tu bot
TOKEN = "8051002066:AAHP7iOF1Sgy-POa7xQWCQyUlRByWbPRkHY"

async def check_webhook():
    # Crea una instancia del bot
    bot = Bot(token=TOKEN)
    
    # Obtiene información del webhook (usa await)
    webhook_info = await bot.get_webhook_info()
    print(f"Webhook info: {webhook_info}")
    
    # Verifica si el webhook está configurado
    if hasattr(webhook_info, 'url') and webhook_info.url == "http://localhost:8000/webhook":
        print("✅ Webhook configurado correctamente")
    else:
        print("❌ Webhook no configurado. Configúralo con:")
        print(f"asyncio.run(bot.set_webhook(url='http://localhost:8000/webhook'))")

# Ejecuta la función asíncrona
asyncio.run(check_webhook())