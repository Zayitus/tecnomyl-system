# setup_webhook.py
import asyncio
from telegram import Bot
import config

async def setup_webhook():
    bot = Bot(token=config.TELEGRAM_TOKEN)
    
    # Cambia esta URL por tu URL de ngrok
    # Ejemplo: https://abc123.ngrok-free.app/webhook
    NGROK_URL = input("Ingresa tu URL de ngrok (ej: https://abc123.ngrok-free.app): ")
    webhook_url = f"{NGROK_URL}/webhook"
    
    try:
        # Configurar webhook
        await bot.set_webhook(url=webhook_url)
        print(f"✅ Webhook configurado: {webhook_url}")
        
        # Verificar configuración
        webhook_info = await bot.get_webhook_info()
        print(f"📋 Info del webhook: {webhook_info}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(setup_webhook())