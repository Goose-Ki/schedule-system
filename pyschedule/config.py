import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '7623252253:AAGhifjn_ctM2yivPErwsNlHdz78SFuxZ9Y')
API_URL = os.getenv('API_URL', 'http://localhost:8080')
