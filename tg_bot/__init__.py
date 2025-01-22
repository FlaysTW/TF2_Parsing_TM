from utils.config import bot, bot_menu
from utils.loging import logger
from parsing import TM_Parsing
import threading
import os
import importlib

class Telegram_Bot():
    @logger.catch()
    def __init__(self, tm: TM_Parsing):
        logger.debug('Starting telegram bot')
        try:
            for x in os.listdir("./tg_bot/handlers/"):
                if x.endswith(".py"):
                    cog = importlib.import_module("tg_bot.handlers." + x[:-3])
                    if x == 'add_item_bd.py':
                        cog.run(bot_menu, tm, True)
                        cog.run(bot, tm)
                    elif x == 'message_item.py':
                        cog.run(bot, tm)
                    else:
                        cog.run(bot_menu, tm)
        except Exception as ex:
            logger.exception(ex)
        logger.debug('Start handlers telegram bot')
        threading.Thread(target=bot.infinity_polling, kwargs={'timeout': 5}).start()
        logger.debug('Start telegram bot')
        threading.Thread(target=bot_menu.infinity_polling, kwargs={'timeout': 5}).start()
        logger.debug('Start telegram menu bot')