from telebot.types import InlineKeyboardButton, Message
from telebot import TeleBot
def cancel(bot: TeleBot,chat_id, message: Message=None):
    if message:
        bot.edit_message_text('Отмена действий!', chat_id, message.message_id)
    else:
        bot.send_message(chat_id, 'Отмена действий!')

def create_button(text: str, callback: str):
    return InlineKeyboardButton(text=text, callback_data=callback)