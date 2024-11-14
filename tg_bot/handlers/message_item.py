from telebot import TeleBot
from telebot.types import CallbackQuery
from utils.loging import logger
from tg_bot.callbacks_data import item_message
from parsing import TM_Parsing
from utils.loading_data import items_bd_list, items_bd_list_unusual, items_cache

def run(bot: TeleBot, tm: TM_Parsing):

    @bot.callback_query_handler(func= lambda x: item_message.filter(type='del').check(x))
    @logger.catch()
    def delete_item_in_cache(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = item_message.parse(callback.data)
        try:
            name = items_cache.pop(f'{data["classid"]}-{data["instanceid"]}')
            mes = callback.message
            mes.text = 'УДАЛЕН ИЗ КЭША!\n' + mes.text
            bot.edit_message_text(mes.text, mes.chat.id, mes.message_id)
            bot.send_message(callback.message.chat.id, f"Предмет <a href='https://t.me/c/{str(callback.message.chat.id)[4:]}/{callback.message.message_thread_id}/{callback.message.message_id}'>{name['name']}</a> успешно удален из кэша!", parse_mode='HTML')
        except:
            bot.send_message(callback.message.chat.id, f"<a href='https://t.me/c/{str(callback.message.chat.id)[4:]}/{callback.message.message_thread_id}/{callback.message.message_id}'>Предмет</a> уже удален из кэша!", parse_mode='HTML')
