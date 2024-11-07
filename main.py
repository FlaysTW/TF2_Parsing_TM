import threading

from tg_bot import Telegram_Bot
from parsing import TM_Parsing
from utils import loading_data

def main():
    tm = TM_Parsing()
    tg = Telegram_Bot(tm)
    #tm.start_thread_parsing_websocket()
    tm.start_parsing()
    tm.start_thread_processing()
    #tm.thread_processing_item('The Ap-Sap', 780611765,11041817)

def test():
    cur = {}
    for i in loading_data.items_bd:
        if i == 'Unusual':
            pass


if __name__ == '__main__':
    main()