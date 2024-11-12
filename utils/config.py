import telebot
import os
from dotenv import load_dotenv
import json

load_dotenv()

bot = telebot.TeleBot(os.getenv('TG_TOKEN'))

with open('./data/config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)
