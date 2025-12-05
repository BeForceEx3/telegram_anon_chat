import os

print("🔍 DEBUG: все переменные окружения:")
print(f"  BOT_TOKEN = '{os.getenv('BOT_TOKEN')}'")
print(f"  ADMIN_ID = '{os.getenv('ADMIN_ID')}'")

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "7911138642"))
DATAPATH = "/app/data/chatdata.json"

print(f"✅ BOT_TOKEN: {'НАЙДЕН' if BOT_TOKEN else 'ОТСУТСТВУЕТ'}")
print(f"✅ ADMIN_ID: {ADMIN_ID}")
