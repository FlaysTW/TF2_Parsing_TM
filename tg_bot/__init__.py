from utils.config import bot
from tg_bot.handler import run
from utils.loging import logger
from parsing import TM_Parsing
import threading

class Telegram_Bot():
    @logger.catch()
    def __init__(self, tm: TM_Parsing):
        logger.debug('Starting telegram bot')
        run(bot, tm)
        threading.Thread(target=bot.infinity_polling, kwargs={'timeout': 5}).start()
        logger.debug('Start telegram bot')