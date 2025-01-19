import threading

from tg_bot import Telegram_Bot
from parsing import TM_Parsing
from utils import loading_data
from utils.loging import logger,create_logger_item, delete_logger_item
def main():
    tm = TM_Parsing()
    tg = Telegram_Bot(tm)
    #tm.start_parsing()
    #tm.bot.start_thread_pool()
    #tm.start_thread_processing()
    #tm.start_thread_parsing_url()
    #tm.start_thread_parsing_websocket()
    #tm.start_thread_save_cache()
    #tm.thread_processing_item("Bill's Hat", 171097181,6260347386)

if __name__ == '__main__':
    main()