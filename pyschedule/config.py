import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '7677286497:AAHEW0AsZOKcacr49dLTD1mcdJoM1kesUmo')
API_URL = os.getenv('API_URL', 'http://localhost:8080')
