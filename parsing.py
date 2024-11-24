import datetime
import threading
import time
import requests
from tg_bot.tg_func import Telegram_functions
from utils.loging import logger
from websockets.sync import client as ws
import json
import queue
from utils.loading_data import items_bd, items_bd_list, items_bd_list_unusual, items_unusual_bd, items_cache, future
from utils.config import config
import csv

class TM_Parsing():
    bot = Telegram_functions()

    parsing_status_url = False
    last_tm_tf2_bd = ''

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

    blacklist_items = []

    def __init__(self):
        logger.debug('Starting parsing')
        self.create_thread_parsing_url()
        self.create_thread_parsing_websocket()
        self.create_thread_processing()
        self.create_thread_save_cache()

    @logger.catch()
    def start_parsing(self):
        self.start_thread_parsing_url()
        self.start_thread_parsing_websocket()
        self.start_thread_processing()
        self.start_thread_save_cache()
        self.bot.start_thread_pool()

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
                    priority = raw['priority']

                    if not any(i in name for i in ['Casemaker']):
                        if any(i in name for i in config['blacklist']):  # TODO: Blacklist
                            self.blacklist_items.append(f'{datetime.datetime.now()}, {name}, {classid}, {instanceid}, https://tf2.tm/en/item/{classid}-{instanceid}')
                            #print(self.blacklist_items)
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

                    threading.Thread(target=self.thread_processing_item, args=[name, classid, instanceid, priority]).start()

                    #print(name, self.items_queue.qsize(), threading.active_count())
                except Exception as ex:
                    logger.exception(ex)
            time.sleep(0.1) #TODO: ИЗМЕНИТЬ на 0.0001
        logger.debug('Stop processing thread')
        logger.debug('Create new thread processing')
        self.create_thread_processing()


    @logger.catch()
    def thread_processing_item(self,name, classid, instanceid, priority):
        r = requests.get(f'https://tf2.tm/api/ItemInfo/{classid}_{instanceid}/en/?key={self.TM_KEY}', timeout=20)
        #print(classid, instanceid)
        #print(r.json())
        if r.status_code == 200:
            resp = r.json()
            item = ""
            full_description = ''
            mes_description = ''
            price_item_raw = float(resp['min_price'])
            price_item = int(resp['min_price']) / 100
            effect = ''
            non_craftable = ''
            quality = False
            message_thread_id = 7
            spell = False
            if resp['description']:
                for des in resp['description']:
                    des_text = des['value']
                    full_description += des_text + '\n'
                    if 'Effect: ' in des_text:
                        effect = des_text.split('Effect: ')[1].strip()
                        continue
                    elif ': ' in des_text and des_text[-1] == ')' and des_text[1] == '(':
                        mes_description += des_text + '\n'
                        continue
                    elif 'Paint Color:' in des_text:
                        mes_description += des_text + '\n'
                        continue
                    elif 'spell only' in des_text and des['color'] == '7ea9d1':
                        mes_description += des_text + '\n'
                        message_thread_id = 5
                        spell = True
                        continue

            if mes_description:
                mes_description = 'Описание:\n' + mes_description + '\n\n'

            if name in items_bd_list or name in items_bd_list_unusual:
                if 'Unusual' == name[:7]:
                    if not spell:
                        message_thread_id = 6
                    if 'Not Usable in Crafting' not in full_description:
                        if 'Craftable' in items_unusual_bd[name]:
                            if effect in items_unusual_bd[name]['Craftable']['Particles']:
                                item = items_unusual_bd[name]['Craftable']['Particles'][effect]
                                price_db = item['price'] * config['currency'][item['currency']]
                    else:
                        if 'Non-Craftable' in items_unusual_bd[name]:
                            if effect in items_unusual_bd[name]['Non-Craftable']['Particles']:
                                item = items_unusual_bd[name]['Non-Craftable']['Particles'][effect]
                                non_craftable = 'Non-Craftable\n'
                                price_db = item['price'] * config['currency'][item['currency']]
                    effect = ' Effect: ' + effect
                else:
                    if 'Not Usable in Crafting' not in full_description:
                        if 'Craftable' in items_bd[name]:
                            item = items_bd[name]['Craftable']
                            price_db = item['price'] * config['currency'][item['currency']]
                    else:
                        if 'Non-Craftable' in items_bd[name]:
                            item = items_bd[name]['Non-Craftable']
                            non_craftable = 'Non-Craftable\n'
                            price_db = item['price'] * config['currency'][item['currency']]

            if any(i in name for i in ['(Field-Tested)', '(Battle Scarred)', '(Well-Worn)', '(Factory New)', '(Minimal Wear)']) and not item:
                quality = True

            if item:
                finily_price = 0
                for filter_price in config['filter']['notification']:
                    if finily_price:
                        break
                    if filter_price == list(config['filter']['notification'])[-1]:
                        finily_price = price_db * ((100 - config['filter']['notification'][filter_price]) / 100)
                    elif price_db <= float(filter_price):
                        finily_price = price_db * (( 100 - config['filter']['notification'][filter_price]) / 100)

                if finily_price or spell or priority:
                    if price_item_raw == -1 and not spell:
                        future['notification'][f'{classid}-{instanceid}'] = {'procent': finily_price * 100 - 1, 'name': name, 'old_price': price_item_raw}
                        items_cache.pop(f'{classid}-{instanceid}')
                    elif price_item <= finily_price or spell or priority:
                        message = f'{name}{effect}\n{non_craftable}\n{mes_description}'

                        message += f'Цена на ТМ: {round(price_item / config["currency"]["keys"], 2)} keys, {price_item} ₽\n'
                        if item['currency'] == 'metal':
                            message +=  f'Цена в базе: {round(item["price"] * config["currency"]["metal"] / config["currency"]["keys"],2)} keys, {round(item["price"] * config["currency"]["metal"],2)} ₽\n'
                        else:
                            message += f'Цена в базе: {item["price"]} keys, {round(item["price"] * config["currency"]["keys"],2)} ₽\n'

                        message += f'\nhttps://tf2.tm/en/item/{classid}-{instanceid}'
                        self.bot.send_item(message, classid, instanceid, price_item_raw, markup_flag=True, message_thread_id=message_thread_id)
                    else:
                        future['notification'][f'{classid}-{instanceid}'] = {'procent': finily_price * 100 - 1, 'name': name, 'old_price': price_item_raw}
                        items_cache.pop(f'{classid}-{instanceid}')
            elif spell:
                message_thread_id = 5
                message = f'{name}{effect}\n{non_craftable}\n{mes_description}'
                message += f'Цена на ТМ: {round(price_item / config["currency"]["keys"], 2)} keys, {price_item} ₽\n\n'
                message += f'https://tf2.tm/en/item/{classid}-{instanceid}'
                self.bot.send_item(message, classid, instanceid, price_item_raw, markup_undefiend=True, message_thread_id=message_thread_id)
            elif quality:
                message_thread_id = 4
                message = f'{name}{effect}\n{non_craftable}\n{mes_description}'
                message += f'Цена на ТМ: {round(price_item / config["currency"]["keys"], 2)} keys, {price_item} ₽\n\n'
                message += f'https://tf2.tm/en/item/{classid}-{instanceid}'
                self.bot.send_item(message, classid, instanceid, price_item_raw, markup_undefiend=True, message_thread_id=message_thread_id)
            else:
                message_thread_id = 3
                message = f'{name}{effect}\n{non_craftable}\n{mes_description}'
                message += f'Цена на ТМ: {round(price_item / config["currency"]["keys"], 2)} keys, {price_item} ₽\n\n'
                message += f'https://tf2.tm/en/item/{classid}-{instanceid}'
                self.bot.send_item(message, classid, instanceid, price_item_raw, markup_undefiend=True, message_thread_id=message_thread_id)
        else:
            pass

    @logger.catch()
    def save_cache(self):
        logger.debug('Start thread save cache')
        while self.status_save_cache:
            try:
                t = items_cache.copy()
                with open('./items/cache.json', 'w', encoding='utf-8') as file:
                    json.dump(t, file, indent=4, ensure_ascii=False)
                logger.success('Successful save cache')
            except Exception as ex:
                logger.error('Thread save cache error')
                logger.exception(ex)
                self.bot.send_message('Ошибка при сохранение кэша!\nОбратитесь к администратору и сделайте дамп кэша!')

            try:
                t = self.blacklist_items.copy()
                text = ''
                for i in t:
                    self.blacklist_items.pop(0)
                    text += i + '\n'
                with open('./items/blacklist.txt', 'a', encoding='utf-8') as file:
                    file.write(text)
                logger.success('Successful blacklist items')
            except Exception as ex:
                logger.error('Thread save cache error')
                logger.exception(ex)
                self.bot.send_message('Ошибка при сохранение предметов в черном списке!\nОбратитесь к администратору и сделайте дамп кэша!')

            try:
                t = future.copy()
                with open('./items/future.json', 'w', encoding='utf-8') as file:
                    json.dump(t, file, indent=4, ensure_ascii=False)
                logger.success('Successful future items')
            except Exception as ex:
                logger.error('Thread save cache error')
                logger.exception(ex)
                self.bot.send_message('Ошибка при сохранение кэша!\nОбратитесь к администратору и сделайте дамп кэша!')
            time.sleep(5)
        logger.debug('Stop thread save cache')
        logger.debug('Create new thread save cache')
        self.create_thread_save_cache()

    @logger.catch()
    def start_thread_save_cache(self):
        if not self.thread_save_cache.is_alive():
            logger.debug('Starting save cache')
            self.status_save_cache = True
            self.thread_save_cache.start()
        else:
            logger.error('Thread save cache working')

    @logger.catch()
    def start_thread_processing(self):
        if not self.parsing_thread_processing_items.is_alive():
            logger.debug('Starting processing')
            self.parsing_status_processing_items = True
            self.parsing_thread_processing_items.start()
        else:
            logger.error('Thread processing working')

    @logger.catch()
    def start_thread_parsing_url(self):
        if not self.parsing_thread_url.is_alive():
            logger.debug('Starting urls parsing')
            self.parsing_status_url = True
            self.parsing_thread_url.start()
        else:
            logger.error('Thread parsing URL working')

    @logger.catch()
    def start_thread_parsing_websocket(self):
        if not self.parsing_thread_websocket.is_alive():
            logger.debug('Starting websockets parsing')
            self.parsing_status_websocket = True
            self.parsing_thread_websocket.start()
        else:
            logger.debug('Thread parsing websocket not created')
            logger.error('Thread parsing websocket working')

    @logger.catch()
    def create_thread_save_cache(self):
        self.thread_save_cache = threading.Thread(target=self.save_cache)
        logger.debug('Thread save cache created successful')

    @logger.catch()
    def create_thread_processing(self):
        self.parsing_thread_processing_items = threading.Thread(target=self.processing_items)
        logger.debug('Thread processing created successful')

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
                r = requests.get('https://tf2.tm/itemdb/current_440.json', timeout=5)
                if r.status_code == 200:
                    tm_tf2_name_file_bd = r.json()['db']
                    if tm_tf2_name_file_bd != self.last_tm_tf2_bd:
                        self.last_tm_tf2_bd = tm_tf2_name_file_bd
                        r = requests.get(f'https://tf2.tm/itemdb/{tm_tf2_name_file_bd}', timeout=5)
                        if r.status_code == 200:
                            raw_tf2_bd = r.text.split('\n')[1:-1]
                            tf2_db = csv.reader(raw_tf2_bd, delimiter=';')
                            for item in tf2_db:
                                classid = item[0]
                                instanceid = item[1]
                                craft = 'Craftable' if item[8] == "1" else 'Non-Craftable'
                                price = float(item[2]) / 100
                                name = item[13]

                                flag = False
                                priority = False
                                flag_autobuy = False
                                if f"{classid}-{instanceid}" not in future['autobuy']:
                                    if f"{classid}-{instanceid}" not in items_cache:
                                        if name in items_bd_list:
                                            if craft in items_bd[name]:
                                                min_price = items_bd[name][craft]['price'] * config['currency'][items_bd[name][craft]['currency']]
                                                finily_price = 0
                                                for filter_price in config['filter']['autobuy']:
                                                    if finily_price:
                                                        break
                                                    if filter_price == list(config['filter']['autobuy'])[-1]:
                                                        finily_price = min_price * ((100 - config['filter']['autobuy'][filter_price]) / 100)
                                                    elif min_price <= float(filter_price):
                                                        finily_price = min_price * (
                                                                (100 - config['filter']['autobuy'][filter_price]) / 100)
                                                #print(price, finily_price, f'{classid}-{instanceid}', name)
                                                if price <= finily_price:
                                                    flag_autobuy = True
                                                    print('Покупаем предмет по фильтру', price, finily_price)
                                        if not flag_autobuy:
                                            if f"{classid}-{instanceid}" not in future['notification']:
                                                flag = True
                                            elif price * 100 <= future['notification'][f"{classid}-{instanceid}"][
                                                'procent']:
                                                priority = True
                                                flag = True
                                                future['notification'].pop(f"{classid}-{instanceid}")
                                elif price * 100 <= future['autobuy'][f"{classid}-{instanceid}"]['procent']:
                                    print("Покупаем предмет")  # Покупка предмета
                                    future['autobuy'].pop(f"{classid}-{instanceid}")

                                if flag:
                                    items_cache[f"{classid}-{instanceid}"] = {'name': name}
                                    self.count_items_url += 1
                                    self.count_items_cache += 1
                                    self.last_item_url = {'name': name, 'id': f"{classid}-{instanceid}",'date': datetime.datetime.now()}
                                    self.items_queue.put({'name': name, 'classid': classid, 'instanceid': instanceid, 'priority': priority})
                        else:
                            logger.error(f'URL ERROR status code {r.status_code}')
                else:
                    logger.error(f'URL ERROR status code {r.status_code}')
            except Exception as ex:
                logger.exception(f'URL {ex}')
            time.sleep(5)
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
                        name = res['i_market_hash_name']
                        classid = res['i_classid']
                        instanceid = res['i_instanceid']
                        price = res['ui_price']

                        flag = False
                        priority = False
                        flag_autobuy = False
                        if f"{classid}-{instanceid}" not in future['autobuy']:
                            if f"{classid}-{instanceid}" not in items_cache:
                                if name in items_bd_list:
                                    min_price = 99999999
                                    for craft in items_bd[name]:
                                        min_price = min(items_bd[name][craft]['price'] * config['currency'][
                                            items_bd[name][craft]['currency']], min_price)
                                    finily_price = 0
                                    for filter_price in config['filter']['autobuy']:
                                        if finily_price:
                                            break
                                        if filter_price == list(config['filter']['autobuy'])[-1]:
                                            finily_price = min_price * (
                                                        (100 - config['filter']['autobuy'][filter_price]) / 100)
                                        elif min_price <= float(filter_price):
                                            finily_price = min_price * (
                                                        (100 - config['filter']['autobuy'][filter_price]) / 100)
                                    if price <= finily_price:
                                        flag_autobuy = True
                                if not flag_autobuy:
                                    if f"{classid}-{instanceid}" not in future['notification']:
                                        flag = True
                                    elif price * 100 <= future['notification'][f"{classid}-{instanceid}"]['procent']:
                                        priority = True
                                        flag = True
                                        future['notification'].pop(f"{classid}-{instanceid}")
                        elif price * 100 <= future['autobuy'][f"{classid}-{instanceid}"]['procent']:
                            print("Покупаем предмет")  # Покупка предмета
                            future['autobuy'].pop(f"{classid}-{instanceid}")

                        if flag:
                            items_cache[f"{classid}-{instanceid}"] = {'name': name}
                            self.count_items_websocket += 1
                            self.count_items_cache += 1
                            self.last_item_websocket = {'name': name, 'id': f"{classid}-{instanceid}", 'date': datetime.datetime.now()}
                            self.items_queue.put({'name': name, 'classid': classid, 'instanceid': instanceid, 'priority': priority})
            except Exception as ex:
                logger.exception(f'WEBSOCKET {ex}')
        logger.debug('Stop thread websocket parsing')
        logger.debug('Create new thread websocket parsing')
        self.create_thread_parsing_websocket()