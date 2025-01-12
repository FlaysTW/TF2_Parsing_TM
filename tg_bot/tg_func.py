import threading
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.util import antiflood
from utils import config
import queue
import time
from utils.loging import logger
from tg_bot.callbacks_data import item_message
from utils.loading_data import items_cache

class Telegram_functions():

    bot = config.bot
    chat_id = -1002330451628

    status_pool = False
    thread_pool: threading.Thread = None

    messages_queue = queue.Queue()

    count_message_not = 0

    def __init__(self):
        self.create_thread_pool()

    @logger.catch()
    def pool_send_items(self):
        logger.debug('Start pool messages')
        while self.status_pool:
            try:
                if not self.messages_queue.empty():
                    kwargs = self.messages_queue.get()
                    if 'write_cache' in kwargs:
                        data_items = kwargs.pop('write_cache')
                        mes = antiflood(self.bot.send_message, **kwargs, number_retries=20)
                        items_cache[f"{data_items['classid']}-{data_items['instanceid']}"]['message'] = mes.json
                        logger.info(f'SEND MESSAGE {data_items["classid"]}-{data_items["instanceid"]} add message to cache message id {mes.message_id}', id=f'{data_items["classid"]}-{data_items["instanceid"]}')
                    else:
                        antiflood(self.bot.send_message, **kwargs, number_retries=20)
                    self.count_message_not -= 1
            except Exception as ex:
                logger.exception(ex)
            time.sleep(0.0001)
        logger.debug('Disable pool messages')
        logger.debug('Create new thread pool messages')
        self.create_thread_pool()

    @logger.catch()
    def start_thread_pool(self):
        if not self.thread_pool.is_alive():
            logger.debug('Starting pool messages')
            self.status_pool = True
            self.thread_pool.start()
        else:
            logger.debug('Thread pool messages working')

    @logger.catch()
    def create_thread_pool(self):
        self.thread_pool = threading.Thread(target=self.pool_send_items)
        logger.debug('Thread pool messages created successful')

    @logger.catch()
    def send_item(self, message, classid, instanceid, price, message_thread_id, markup_flag=False, markup_undefiend=False):
        if markup_flag:
            data_item = {'classid': classid, 'instanceid': instanceid, 'price': price}
            markup = InlineKeyboardMarkup()
            buttons = [InlineKeyboardButton(text='Купить', callback_data=item_message.new(**data_item, type='buy')),
                       InlineKeyboardButton(text='Удалить из кэша', callback_data=item_message.new(**data_item, type='del')),
                       InlineKeyboardButton(text='Добавить предмет в ПНБ', callback_data=item_message.new(**data_item, type='pnb'))]
            markup.add(buttons[0], buttons[1])
            markup.add(buttons[2])
            self.messages_queue.put({'chat_id': self.chat_id, 'text': message, 'message_thread_id': message_thread_id, 'reply_markup': markup, 'write_cache': data_item})
        elif markup_undefiend:
            data_item = {'classid': classid, 'instanceid': instanceid, 'price': price}
            markup = InlineKeyboardMarkup()
            buttons = [InlineKeyboardButton(text='Удалить из кэша', callback_data=item_message.new(**data_item, type='del')),
                       InlineKeyboardButton(text='Добавить в базу данных', callback_data=item_message.new(**data_item, type='add_bd'))]
            markup.add(*buttons)
            self.messages_queue.put({'chat_id': self.chat_id, 'text': message, 'message_thread_id': message_thread_id, 'reply_markup': markup, 'write_cache': data_item})
        else:
            self.messages_queue.put({'chat_id': self.chat_id, 'text': message, 'message_thread_id': message_thread_id})

        self.count_message_not += 1

    @logger.catch()
    def send_message(self, message):
        self.messages_queue.put({'chat_id': self.chat_id, 'text': message})
        self.count_message_not += 1

