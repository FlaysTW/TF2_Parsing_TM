import datetime
import threading
import time
import requests
from tg_bot.tg_func import Telegram_functions
from utils.loging import logger
from websockets.sync import client as ws
import json
import queue
from utils.loading_data import items_bd, items_bd_list, items_bd_list_unusual, items_unusual_bd, items_cache
from utils.config import config


class TM_Parsing():
    bot = Telegram_functions()

    parsing_status_url = False
    parsing_url_num = 0

    parsing_status_websocket = False

    parsing_thread_url: threading.Thread = None
    parsing_thread_websocket: threading.Thread = None

    items_queue = queue.Queue()

    parsing_thread_processing_items: threading.Thread = None
    parsing_status_processing_items = True

    TM_KEY = 'w15eJM678BP8FrcukaujhTCQ66J823M'

    count_items_url = 0
    count_items_websocket = 0

    thread_save_cache: threading.Thread = None
    status_save_cache = True

    count_items_cache = len(list(items_cache))

    datetime.datetime.now().strftime("%H:%M:%S %d/%m")

    last_item_url = {'name': None, 'id': '0-0', 'date': datetime.datetime.now()}
    last_item_websocket = {'name': None, 'id': '0-0', 'date': datetime.datetime.now()}

    def __init__(self):
        logger.debug('Starting parsing')
        self.create_thread_parsing_url()
        self.create_thread_parsing_websocket()
        self.create_thread_processing()
        self.create_thread_save_cache()

    @logger.catch()
    def processing_items(self):
        logger.debug('Start processing Thread')
        while self.parsing_status_processing_items:
            if not self.items_queue.empty():
                try:
                    raw = self.items_queue.get()
                    name = raw['name']
                    classid = raw['classid']
                    instanceid = raw['instanceid']

                    if any(i in name for i in['(Field-Tested)', '(Battle Scarred)', '(Well-Worn)', '(Factory New)', '(Minimal Wear)']):  # TODO: Quality
                        self.bot.send_item(f'{name}, {classid}, {instanceid}', classid, instanceid, 4)
                        continue

                    if not any(i in name for i in ['Casemaker']):
                        if any(i in name for i in ['kit', 'Kit', 'Tour of Duty Ticket', 'Mann Co. Supply Crate Key', 'Refined Metal', ' Case', 'Create', 'Mann Co. Supply Munition']):  # TODO: Blacklist
                            continue

                    for repl in ['Series ']:
                        name = name.replace(repl, '')
                    if not any(i in name for i in
                               ['The Bitter Taste of Defeat and Lime', 'The Essential Accessories',
                                'The Value of Teamwork', 'The Concealed Killer Weapons Case',
                                "The Color of a Gentlemann's Business Pants", 'The Athletic Supporter', 'The Superfan',
                                'The Powerhouse Weapons Case']):
                        if 'The ' == name[:4] or 'the ' == name[:4]:
                            name = name[4:]

                    threading.Thread(target=self.thread_processing_item, args=[name, classid, instanceid]).start()

                    #print(name, self.items_queue.qsize(), threading.active_count())
                except Exception as ex:
                    logger.exception(ex)
            time.sleep(0.0001)
        logger.debug('Stop processing thread')
        logger.debug('Create new thread processing')
        self.create_thread_processing()


    @logger.catch()
    def thread_processing_item(self,name, classid, instanceid, quality=False):
        r = requests.get(f'https://tf2.tm/api/ItemInfo/{classid}_{instanceid}/en/?key={self.TM_KEY}', timeout=5)
        #print(classid, instanceid)
        #print(r.json())
        if r.status_code == 200:
            resp = r.json()
            item = ""
            full_description = ''
            mes_description = ''
            price_item = int(resp['min_price']) / 100
            effect = ''
            if resp['description']:
                for des in resp['description']:
                    des = des['value']
                    full_description += des + '\n'
                    if 'Effect: ' in des:
                        effect = des.split('Effect: ')[1].strip()
                        continue
                    elif ': ' in des and des[-1] == ')' and des[1] == '(':
                        mes_description += des + '\n'
                        continue
                    elif 'Paint Color:' in des:
                        mes_description += des + '\n'
                        continue
                    elif 'spell only' in des:
                        mes_description += des + '\n'
                        continue

            if mes_description:
                mes_description = 'Описание:\n' + mes_description + '\n\n'
            if name in items_bd_list or name in items_bd_list_unusual:
                if 'Unusual' == name[:7]:
                    if 'Not Usable in Crafting' not in full_description:
                        if 'Craftable' in items_unusual_bd[name]:
                            if effect in items_unusual_bd[name]['Craftable']['Particles']:
                                item = items_unusual_bd[name]['Craftable']['Particles'][effect]
                                price_db = item['price'] * config['currency'][item['currency']]
                            else:
                                self.bot.send_item(f'{name}, {classid}, {instanceid}', classid, instanceid, 3)
                        else:
                            self.bot.send_item(f'{name}, {classid}, {instanceid}', classid, instanceid, 3)
                    else:
                        if 'Non-Craftable' in items_unusual_bd[name]:
                            if effect in items_unusual_bd[name]['Non-Craftable']['Particles']:
                                item = items_unusual_bd[name]['Non-Craftable']['Particles'][effect]
                                print(item, effect)
                                price_db = item['price'] * config['currency'][item['currency']]
                            else:
                                self.bot.send_item(f'{name}, {classid}, {instanceid}', classid, instanceid, 3)
                        else:
                            self.bot.send_item(f'{name}, {classid}, {instanceid}', classid, instanceid, 3)
                    effect = ' Effect: ' + effect
                else:
                    if 'Not Usable in Crafting' not in full_description:
                        if 'Craftable' in items_bd[name]:
                            item = items_bd[name]['Craftable']
                            price_db = item['price'] * config['currency'][item['currency']]
                        else:
                            self.bot.send_item(name, classid, instanceid, 3)
                    else:
                        if 'Non-Craftable' in items_bd[name]:
                            item = items_bd[name]['Non-Craftable']
                            price_db = item['price'] * config['currency'][item['currency']]
                        else:
                            self.bot.send_item(name, classid, instanceid, 3)
            if item:
                if price_item <= price_db * 0.9:
                    message = f'{name}{effect}\n\n{mes_description}'

                    message += f'Цена на ТМ: {round(price_item / config["currency"]["keys"], 2)} keys, {price_item} ₽\n'
                    if item['currency'] == 'metal':
                        message +=  f'Цена в базе: {item["price"] * config["currency"]["metal"] / config["currency"]["keys"]} keys, {round(item["price"] * config["currency"]["metal"],2)} ₽\n'
                    else:
                        message += f'Цена в базе: {item["price"]} keys, {item["price"] * config["currency"]["keys"]} ₽\n'

                    message += f'\nhttps://tf2.tm/en/item/{classid}-{instanceid}'

                    self.bot.send_item(message, classid, instanceid, markup_flag=True, message_thread_id=7)
            else:
                self.bot.send_item(f'{name}, {classid}, {instanceid}', classid, instanceid, 3)

        else:
            pass



    @logger.catch()
    def start_parsing(self):
        self.start_thread_parsing_url()
        self.start_thread_parsing_websocket()
        self.start_thread_processing()
        self.start_thread_save_cache()

    @logger.catch()
    def start_thread_save_cache(self):
        if not self.thread_save_cache.is_alive():
            logger.debug('Starting save cache')
            self.thread_save_cache.start()
        else:
            logger.error('Thread save cache working')

    @logger.catch()
    def create_thread_save_cache(self):
        self.thread_save_cache = threading.Thread(target=self.save_cache)
        logger.debug('Thread save cache created successful')

    @logger.catch()
    def save_cache(self):
        logger.debug('Start thread save cache')
        while self.status_save_cache:
            try:
                with open('./items/cache.json', 'w', encoding='utf-8') as file:
                    json.dump(items_cache, file, indent=4, ensure_ascii=False)
                logger.success('Successful save cache')
            except Exception as ex:
                logger.error('Thread save cache error')
                logger.exception(ex)
                self.bot.send_message('Ошибка при сохранение кэша!\nОбратитесь к администратору и сделайте дамп кэша!')
            time.sleep(5)
        logger.debug('Stop thread save cache')
        logger.debug('Create new thread save cache')
        self.create_thread_save_cache()


    @logger.catch()
    def start_thread_processing(self):
        if not self.parsing_thread_processing_items.is_alive():
            logger.debug('Starting processing')
            self.parsing_thread_processing_items.start()
        else:
            logger.error('Thread processing working')

    @logger.catch()
    def create_thread_processing(self):
        self.parsing_thread_processing_items = threading.Thread(target=self.processing_items)
        logger.debug('Thread processing created successful')

    @logger.catch()
    def start_thread_parsing_url(self):
        if not self.parsing_thread_url.is_alive():
            if self.parsing_status_url == False:
                logger.debug('Starting urls parsing')
                self.parsing_status_url = True
                self.parsing_thread_url.start()
        else:
            logger.error('Thread parsing URL working')

    @logger.catch()
    def start_thread_parsing_websocket(self):
        if not self.parsing_thread_websocket.is_alive():
            if self.parsing_status_websocket == False:
                logger.debug('Starting websockets parsing')
                self.parsing_status_websocket = True
                self.parsing_thread_websocket.start()
        else:
            logger.debug('Thread parsing websocket not created')
            logger.error('Thread parsing websocket working')

    @logger.catch()
    def create_thread_parsing_url(self):
        self.parsing_thread_url = threading.Thread(target=self.parsing_url)
        logger.debug('Thread created URL successful')

    @logger.catch()
    def create_thread_parsing_websocket(self):
        self.parsing_thread_websocket = threading.Thread(target=self.parsing_websocket)
        logger.debug('Thread created WEBSOCKET successful')

    @logger.catch()
    def parsing_url(self):
        logger.debug('Start thread urls parsing')
        while self.parsing_status_url:
            try:
                url = f"https://tf2.tm/ajax/name/all/all/all/{self.parsing_url_num}/56/0;500000/all/all/-1/-1/all?sd=desc"
                response = requests.get(url, timeout=5)
                if response.status_code == 500:
                    self.parsing_url_num = 0
                elif response.status_code == 200:
                    for item in response.json()[0]:
                        if f"{item[0]}-{item[1]}" not in items_cache:
                            items_cache[f"{item[0]}-{item[1]}"] = {'name': item[-1]}
                            self.count_items_url += 1
                            self.count_items_cache += 1
                            self.last_item_url = {'name': item[-1], 'id': f"{item[0]}-{item[1]}", 'date': datetime.datetime.now()}
                            self.items_queue.put({'name': item[-1], 'classid': item[0], 'instanceid': item[1]})
                    self.parsing_url_num += 1
                else:
                    logger.error(f'URL ERROR status code {response.status_code} number page - {self.parsing_url_num}')
            except Exception as ex:
                logger.exception(f'URL {ex}')
        logger.debug('Stop thread urls parsing')
        logger.debug('Create new thread urls parsing')
        self.create_thread_parsing_url()

    @logger.catch()
    def parsing_websocket(self):
        logger.debug('Start thread websocket parsing')
        while self.parsing_status_websocket:
            try:
                with ws.connect('wss://wsnn.dota2.net/wsn/', open_timeout=5, close_timeout=5) as client:
                    logger.success(f'WEBSOCKET SUCCEFULL CONNECTION')
                    client.send('newitems_tf')
                    while self.parsing_status_websocket:
                        res = json.loads(json.loads(client.recv(timeout=10))['data'])
                        if f"{res['i_classid']}-{res['i_instanceid']}" not in items_cache:
                            items_cache[f"{res['i_classid']}-{res['i_instanceid']}"] = {'name': res['i_market_hash_name']}
                            self.count_items_websocket += 1
                            self.count_items_cache += 1
                            self.last_item_websocket = {'name': res['i_market_hash_name'], 'id': f"{res['i_classid']}-{res['i_instanceid']}", 'date': datetime.datetime.now()}
                            self.items_queue.put({'name': res['i_market_hash_name'], 'classid': res['i_classid'], 'instanceid': res['i_instanceid']})
            except Exception as ex:
                logger.exception(f'WEBSOCKET {ex}')
        logger.debug('Stop thread websocket parsing')
        logger.debug('Create new thread websocket parsing')
        self.create_thread_parsing_websocket()