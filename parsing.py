import time
import requests
from tg_bot.tg_func import Telegram_functions
from utils.loging import logger
from websockets.sync import client as ws
import json


class TM_Parsing():
    bot = Telegram_functions()

    parsing_status_url = True
    parsing_url_num = 0

    parsing_status_websocket = True

    def __init__(self):
        logger.debug('Starting parsing')

    @logger.catch()
    def start_parsing_url(self):
        while self.parsing_status_url:
            try:
                url = f"https://tf2.tm/ajax/name/all/all/all/{self.parsing_url_num}/56/0;500000/all/all/-1/-1/all?sd=desc"
                response = requests.get(url, timeout=5)
                if response.status_code == 500:
                    self.parsing_url_num = 0
                elif response.status_code == 200:
                    logger.info(f'URL {response.json()}')
                self.parsing_url_num += 1
            except Exception as ex:
                logger.exception(f'{ex}')

    @logger.catch()
    def start_parsing_websocket(self):
        while self.parsing_status_websocket:
            try:
                with ws.connect('wss://wsnn.dota2.net/wsn/', open_timeout=5, close_timeout=5) as client:
                    logger.success(f'WEBSOCKET SUCCEFULL CONNECTION')
                    client.send('newitems_tf')
                    while self.parsing_status_websocket:
                        res = json.loads(json.loads(client.recv(timeout=5))['data'])
                        logger.info(f'WEBSOCKET {res}')
            except Exception as ex:
                logger.exception(f'{ex}')