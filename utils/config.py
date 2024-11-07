import telebot
import os
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv('TG_TOKEN'))

config = {'currency': {'metal': 2.9, 'keys': 171.0}}