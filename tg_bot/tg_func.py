from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

class Telegram_functions():

    def test(self):
        print('test')

    def send_item(self, bot: TeleBot, message, classid, instanceid, message_thread_id):
        markup = InlineKeyboardMarkup()
        but1 = InlineKeyboardButton(text=1)