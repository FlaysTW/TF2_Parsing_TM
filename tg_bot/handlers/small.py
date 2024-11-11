from telebot import TeleBot
from telebot.types import Message
from parsing import TM_Parsing

def run(bot: TeleBot, tm: TM_Parsing):
    @bot.message_handler(commands=['stop'])
    def stop(message: Message):
        tm.status_save_cache = False
        tm.parsing_status_url = False
        tm.parsing_status_websocket = False
        tm.parsing_status_processing_items = False
        tm.bot.status_pool = False