import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '7957730475:AAH10Q5MX9aTefw1xrDhrGfJ4JTJHLYf1gQ')
API_URL = os.getenv('API_URL', 'http://localhost:8080')
