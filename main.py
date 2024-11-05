import threading

from tg_bot import Telegram_Bot
from parsing import TM_Parsing
from utils import loading_data

def main():
    #tg = Telegram_Bot()
    tm = TM_Parsing()
    threading.Thread(target=tm.start_parsing_websocket).start()
    threading.Thread(target=tm.start_parsing_url).start()

def test():
    maxim = 0
    word = ''
    for i in loading_data.items_bd:
        if len(i) >= maxim:
            maxim = len(i)
            word = i

    print(maxim, word)

if __name__ == '__main__':
    main()