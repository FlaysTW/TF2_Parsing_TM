import threading
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.util import antiflood
from utils import config
import queue
import time
from utils.loging import logger
from tg_bot.callbacks_data import item_message

class Telegram_functions():

    bot = config.bot
    chat_id = -1002330451628

    status_pool = True
    thread_pool: threading.Thread = None

    messages_queue = queue.Queue()

    def __init__(self):
        self.start_thread_pool()

    @logger.catch()
    def pool_send_items(self):
        logger.debug('Start pool messages')
        while self.status_pool:
            try:
                if not self.messages_queue.empty():
                    antiflood(self.bot.send_message, **self.messages_queue.get(), number_retries=20)
            except Exception as ex:
                logger.exception(ex)
            time.sleep(0.0001)
        logger.debug('Disable pool messages')

    @logger.catch()
    def start_thread_pool(self):
        if self.thread_pool:
            logger.debug('Starting pool messages')
            self.thread_pool.start()
        else:
            logger.debug('Thread pool messages not created')
            self.create_thread_pool()
            self.start_thread_pool()

    @logger.catch()
    def create_thread_pool(self):
        self.thread_pool = threading.Thread(target=self.pool_send_items)
        logger.debug('Thread pool messages created successful')

    @logger.catch()
    def send_item(self, message, classid, instanceid, message_thread_id, markup_flag=False, markup_undefiend=False):
        if markup_flag:
            data_item = {'classid': classid, 'instanceid': instanceid}
            markup = InlineKeyboardMarkup()
            buttons = [InlineKeyboardButton(text='Купить', callback_data=item_message.new(**data_item, type='buy')),
                       InlineKeyboardButton(text='Удалить из кэша', callback_data=item_message.new(**data_item, type='del')),
                       InlineKeyboardButton(text='Прислать если цена понизится', callback_data=item_message.new(**data_item, type='not')),
                       InlineKeyboardButton(text='Купить если цена понизится', callback_data=item_message.new(**data_item, type='buyo'))]
            markup.add(buttons[0], buttons[1])
            markup.add(buttons[2])
            markup.add(buttons[3])
            self.messages_queue.put({'chat_id': self.chat_id, 'text': message, 'message_thread_id': message_thread_id, 'reply_markup': markup})
        elif markup_undefiend:
            data_item = {'classid': classid, 'instanceid': instanceid}
            markup = InlineKeyboardMarkup()
            buttons = [InlineKeyboardButton(text='Удалить из кэша', callback_data=item_message.new(**data_item, type='del')),
                       InlineKeyboardButton(text='Добавить в базу данных', callback_data=item_message.new(**data_item, type='add_bd'))]
            markup.add(*buttons)
            self.messages_queue.put({'chat_id': self.chat_id, 'text': message, 'message_thread_id': message_thread_id, 'reply_markup': markup})
        else:
            self.messages_queue.put({'chat_id': self.chat_id, 'text': message, 'message_thread_id': message_thread_id})

    @logger.catch()
    def send_message(self, message):
        self.messages_queue.put({'chat_id': self.chat_id, 'text': message})

