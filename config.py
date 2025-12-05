import os

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
DATA_PATH = '/tmp/chat_data.json'  # Render tmp/
