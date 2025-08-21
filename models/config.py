# config.py
import os
from dotenv import load_dotenv

load_dotenv()  # Opcional, si usas variables de entorno

# Configuración de Telegram
TELEGRAM_TOKEN = "8051002066:AAHP7iOF1Sgy-POa7xQWCQyUlRByWbPRkHY"  # Tu token

# Configuración de la base de datos (SQLite)
DATABASE_URL = "sqlite:///./test.db"  