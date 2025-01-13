import datetime
import threading
import time
import requests
from tg_bot.tg_func import Telegram_functions
from utils.loging import logger, create_logger_item, delete_logger_item
from websockets.sync import client as ws
import json
import queue
from utils.loading_data import items_bd, items_bd_list, items_bd_list_unusual, items_unusual_bd, items_cache, future
from utils.config import config
import csv
import copy

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

    TM_KEY = config['api_key']

    TM_BALANCE = 0
    TM_BALANCE_TIME = 0
    TM_STEAM64 = 0
    TM_CURRENCY = 'RUB'

    count_items_url = 0
    count_items_websocket = 0

    thread_save_cache: threading.Thread = None
    status_save_cache = True

    count_items_cache = len(list(items_cache))

    datetime.datetime.now().strftime("%H:%M:%S %d/%m")

    last_item_url = {'name': None, 'id': '0-0', 'date': datetime.datetime.now()}
    last_item_websocket = {'name': None, 'id': '0-0', 'date': datetime.datetime.now()}

    blacklist_items = []

    autobuy_spell = False
    autobuy_unusual = False
    autobuy_all_items = False

    def __init__(self):
        logger.debug('Starting parsing')
        self.get_balance()
        self.get_steam64()
        self.create_thread_parsing_url()
        self.create_thread_parsing_websocket()
        self.create_thread_processing()
        self.create_thread_save_cache()

    def buy_item(self, classid, instanceid, price, description = '', title = ''):
        url = 'ofdpkt'
        if title:
            name = title
        else:
            name = items_cache[f"{classid}-{instanceid}"]["name"]
        mes = (f'Покупка предмета!\n'
               f'Название предмета: {name}\n'
               f'Айди предмета: {classid}-{instanceid}'
               f'Цена на ТМ: {price}\n'
               f'{description}')
        self.bot.send_item(mes, classid, instanceid, price, 2)

    def get_balance(self):
        response = requests.get(f'https://tf2.tm/api/v2/get-money?key={self.TM_KEY}')
        logger.debug('Getting balance TM')
        if response.status_code == 200:
            result = response.json()
            if result['success'] == True:
                logger.debug(f'Get balance TM Balance: {result["money"]} {result["currency"]}')
                self.TM_BALANCE = result['money']
                self.TM_CURRENCY = result['currency']
                self.TM_BALANCE_TIME = datetime.datetime.now()
            else:
                logger.error(f'Getting balance status error {result}')
        else:
            logger.error(f'Getting balance error status code {response.status_code}')

    def get_steam64(self):
        response = requests.get(f'https://tf2.tm/api/v2/get-my-steam-id?key={self.TM_KEY}')
        logger.debug('Getting steam64')
        if response.status_code == 200:
            result = response.json()
            if result['success'] == True:
                logger.debug(f'Get steam64 TM {result["steamid64"]}')
                self.TM_STEAM64 = result['steamid64']
            else:
                logger.error(f'Getting steam64 status error {result}')
        else:
            logger.error(f'Getting steam64 error status code {response.status_code}')

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
                    logger.info(f'PROCCESING ITEM new {classid}-{instanceid}', id=f'{classid}-{instanceid}')
                    if not any(i in name for i in ['Casemaker']):
                        if any(i in name for i in config['blacklist']):  # TODO: Blacklist
                            logger.info(f'PROCCESING ITEM {classid}-{instanceid} add blacklist', id=f'{classid}-{instanceid}')
                            self.blacklist_items.append(f'{datetime.datetime.now()}, {name}, {classid}, {instanceid}, https://tf2.tm/en/item/{classid}-{instanceid}')
                            #print(self.blacklist_items)
                            delete_logger_item(f'{classid}-{instanceid}')
                            continue

                    for repl in ['Series ']:
                        name = name.replace(repl, '')

                    logger.info(f'PROCCESING ITEM {classid}-{instanceid} replacing name item New name: {name}', id=f'{classid}-{instanceid}')

                    if not any(i in name for i in
                               ['The Bitter Taste of Defeat and Lime', 'The Essential Accessories',
                                'The Value of Teamwork', 'The Concealed Killer Weapons Case',
                                "The Color of a Gentlemann's Business Pants", 'The Athletic Supporter', 'The Superfan',
                                'The Powerhouse Weapons Case']):
                        if 'The ' == name[:4] or 'the ' == name[:4]:
                            name = name[4:]
                            logger.info(f'PROCCESING ITEM {classid}-{instanceid} replacing name item New name: {name}', id=f'{classid}-{instanceid}')

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
        logger.info(f'PROCCESING ITEM {classid}-{instanceid} getting item info', id=f'{classid}-{instanceid}')
        if r.status_code == 200:
            logger.success(f'PROCCESING ITEM {classid}-{instanceid} get item info', id=f'{classid}-{instanceid}')
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
            logger.info(f'PROCCESING ITEM {classid}-{instanceid} check description', id=f'{classid}-{instanceid}')
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
            logger.info(f'PROCCESING ITEM {classid}-{instanceid} full description: {full_description}', id=f'{classid}-{instanceid}')
            logger.info(f'PROCCESING ITEM {classid}-{instanceid} unusual effect: {effect}', id=f'{classid}-{instanceid}')
            logger.info(f'PROCCESING ITEM {classid}-{instanceid} spell: {spell}', id=f'{classid}-{instanceid}')

            if mes_description:
                mes_description = 'Описание:\n' + mes_description + '\n\n'

            logger.info(f'PROCCESING ITEM {classid}-{instanceid} check item in bd', id=f'{classid}-{instanceid}')
            if name in items_bd_list or name in items_bd_list_unusual:
                logger.info(f'PROCCESING ITEM {classid}-{instanceid} item in bd', id=f'{classid}-{instanceid}')
                if 'Unusual' == name[:7]:
                    logger.info(f'PROCCESING ITEM {classid}-{instanceid} check item in unusual bd', id=f'{classid}-{instanceid}')
                    if not spell:
                        message_thread_id = 6
                    if 'Not Usable in Crafting' not in full_description:
                        if 'Craftable' in items_unusual_bd[name]:
                            if effect in items_unusual_bd[name]['Craftable']['Particles']:
                                item = items_unusual_bd[name]['Craftable']['Particles'][effect]
                                price_db = item['price'] * config['currency'][item['currency']]
                            else:
                                logger.warning(f'PROCCESING ITEM {classid}-{instanceid} Effect not in Craftable unusual bd item {name} Effect: {effect}', id=f'{classid}-{instanceid}')
                        else:
                            logger.warning(f'PROCCESING ITEM {classid}-{instanceid} Craftable not in unusual bd item {name}', id=f'{classid}-{instanceid}')
                    else:
                        if 'Non-Craftable' in items_unusual_bd[name]:
                            if effect in items_unusual_bd[name]['Non-Craftable']['Particles']:
                                item = items_unusual_bd[name]['Non-Craftable']['Particles'][effect]
                                non_craftable = 'Non-Craftable\n'
                                price_db = item['price'] * config['currency'][item['currency']]
                            else:
                                logger.warning(f'PROCCESING ITEM {classid}-{instanceid} Effect not in Non-Craftable unusual bd item {name} Effect: {effect}', id=f'{classid}-{instanceid}')
                        else:
                            logger.warning(f'PROCCESING ITEM {classid}-{instanceid} Non-Craftable not in unusual bd item {name}', id=f'{classid}-{instanceid}')
                    effect = ' Effect: ' + effect
                else:
                    if 'Not Usable in Crafting' not in full_description:
                        if 'Craftable' in items_bd[name]:
                            item = items_bd[name]['Craftable']
                            price_db = item['price'] * config['currency'][item['currency']]
                        else:
                            logger.warning(f'PROCCESING ITEM {classid}-{instanceid} Craftable not in bd item {name}', id=f'{classid}-{instanceid}')
                    else:
                        if 'Non-Craftable' in items_bd[name]:
                            item = items_bd[name]['Non-Craftable']
                            non_craftable = 'Non-Craftable\n'
                            price_db = item['price'] * config['currency'][item['currency']]
                        else:
                            logger.warning(f'PROCCESING ITEM {classid}-{instanceid} Non-Craftable not in bd item {name}', id=f'{classid}-{instanceid}')
            else:
                logger.warning(f'PROCCESING ITEM {classid}-{instanceid} not in item bd', id=f'{classid}-{instanceid}')

            if any(i in name for i in ['(Field-Tested)', '(Battle Scarred)', '(Well-Worn)', '(Factory New)', '(Minimal Wear)']) and not item:
                quality = True

            logger.info(f'PROCCESING ITEM {classid}-{instanceid} check quality: {quality}', id=f'{classid}-{instanceid}')

            if item:
                flag_autobuy = False
                autobuy_price = 0
                filter_price_log = 0
                for filter_price in config['filter']['autobuy']:
                    if autobuy_price:
                        break
                    if filter_price == list(config['filter']['autobuy'])[-1]:
                        filter_price_log = filter_price
                        autobuy_price = price_db * ((100 - config['filter']['autobuy'][filter_price]) / 100)
                    elif price_db <= float(filter_price):
                        filter_price_log = filter_price
                        autobuy_price = price_db * ((100 - config['filter']['autobuy'][filter_price]) / 100)
                logger.info(f'PROCCESING ITEM {classid}-{instanceid} find autobuy filter price: {filter_price_log} Procent filter: {config["filter"]["autobuy"][filter_price_log]} New price: {autobuy_price} BD price: {price_db} Price item: {price_item}', id=f'{classid}-{instanceid}')

                if price_item <= autobuy_price and price_item_raw >= 0:
                    flag_autobuy = True
                    print('Покупаем предмет по фильтру', price_item, autobuy_price)

                if flag_autobuy:
                    logger.info(f'PROCCESING ITEM {classid}-{instanceid} filter autobuy item Price TM: {price_item} Price DB: {price_db}', id=f'{classid}-{instanceid}')
                    logger.info('Попытка купить предмет!')
                    description = (f'Цена в базе: {price_db}\n'
                                   f'Фильтр: {filter_price_log}\n'
                                   f'Процент: {config["filter"]["autobuy"][filter_price_log]} %'
                                   f'Цена в базе с фильтром: {autobuy_price}\n')
                    self.buy_item(classid, instanceid, price_item, description)

                filter_price_log = 0
                finily_price = 0
                for filter_price in config['filter']['notification']:
                    if finily_price:
                        break
                    if filter_price == list(config['filter']['notification'])[-1]:
                        filter_price_log = filter_price
                        finily_price = price_db * ((100 - config['filter']['notification'][filter_price]) / 100)
                    elif price_db <= float(filter_price):
                        filter_price_log = filter_price
                        finily_price = price_db * (( 100 - config['filter']['notification'][filter_price]) / 100)

                logger.info(f'PROCCESING ITEM {classid}-{instanceid} find notification filter price: {filter_price_log} Procent filter: {config["filter"]["notification"][filter_price_log]} New price: {finily_price} BD price: {price_db} Price item: {price_item}', id=f'{classid}-{instanceid}')

                if finily_price or spell or priority:
                    if price_item_raw == -1 and not spell:
                        finily_price = -10000
                        if price_db >= 500:
                            logger.info(f'PROCCESING ITEM {classid}-{instanceid} get priority Price db: {price_db}', id=f'{classid}-{instanceid}')
                            priority = True
                        logger.info(f'PROCCESING ITEM {classid}-{instanceid} change price check for -1', id=f'{classid}-{instanceid}')

                    if price_item <= finily_price or spell or priority:
                        logger.success(f'PROCCESING ITEM {classid}-{instanceid} send message in telegram in chanel id: {message_thread_id}', id=f'{classid}-{instanceid}')
                        message = f'{name}{effect}\n{non_craftable}\n{mes_description}'

                        message += f'Цена на ТМ: {round(price_item / config["currency"]["keys"], 2)} keys, {price_item} ₽\n'
                        if item['currency'] == 'metal':
                            message +=  f'Цена в базе: {round(item["price"] * config["currency"]["metal"] / config["currency"]["keys"],2)} keys, {round(item["price"] * config["currency"]["metal"],2)} ₽\n'
                        else:
                            message += f'Цена в базе: {item["price"]} keys, {round(item["price"] * config["currency"]["keys"],2)} ₽\n'

                        message += f'\nhttps://tf2.tm/en/item/{classid}-{instanceid}'
                        self.bot.send_item(message, classid, instanceid, price_item_raw, markup_flag=True, message_thread_id=message_thread_id)
                    else:
                        logger.info(f'PROCCESING ITEM {classid}-{instanceid} add to future notification Price: {finily_price * 100 - 1} Old price: {price_item_raw}', id=f'{classid}-{instanceid}')
                        future['notification'][f'{classid}-{instanceid}'] = {'procent': finily_price * 100 - 1, 'name': name, 'old_price': price_item_raw}
                        items_cache.pop(f'{classid}-{instanceid}')
            elif spell:
                message_thread_id = 5
                logger.success(f'PROCCESING ITEM {classid}-{instanceid} send message in telegram in chanel id: {message_thread_id}', id=f'{classid}-{instanceid}')
                message = f'{name}{effect}\n{non_craftable}\n{mes_description}'
                message += f'Цена на ТМ: {round(price_item / config["currency"]["keys"], 2)} keys, {price_item} ₽\n\n'
                message += f'https://tf2.tm/en/item/{classid}-{instanceid}'
                self.bot.send_item(message, classid, instanceid, price_item_raw, markup_undefiend=True, message_thread_id=message_thread_id)
            elif quality:
                message_thread_id = 4
                logger.success(f'PROCCESING ITEM {classid}-{instanceid} send message in telegram in chanel id: {message_thread_id}', id=f'{classid}-{instanceid}')
                message = f'{name}{effect}\n{non_craftable}\n{mes_description}'
                message += f'Цена на ТМ: {round(price_item / config["currency"]["keys"], 2)} keys, {price_item} ₽\n\n'
                message += f'https://tf2.tm/en/item/{classid}-{instanceid}'
                self.bot.send_item(message, classid, instanceid, price_item_raw, markup_undefiend=True, message_thread_id=message_thread_id)
            else:
                message_thread_id = 3
                logger.success(f'PROCCESING ITEM {classid}-{instanceid} send message in telegram in chanel id: {message_thread_id}', id=f'{classid}-{instanceid}')
                message = f'{name}{effect}\n{non_craftable}\n{mes_description}'
                message += f'Цена на ТМ: {round(price_item / config["currency"]["keys"], 2)} keys, {price_item} ₽\n\n'
                message += f'https://tf2.tm/en/item/{classid}-{instanceid}'
                self.bot.send_item(message, classid, instanceid, price_item_raw, markup_undefiend=True, message_thread_id=message_thread_id)
        else:
            logger.error(f'PROCCESING ITEM {classid}-{instanceid} get info item ERROR', id=f'{classid}-{instanceid}')
        delete_logger_item(f'{classid}-{instanceid}')

    @logger.catch()
    def save_cache(self):
        logger.debug('Start thread save cache')
        while self.status_save_cache:
            try:
                t1 = {**items_cache}
                with open('./items/cache.json', 'w', encoding='utf-8') as file:
                    json.dump(t1, file, indent=4, ensure_ascii=False)
                logger.success('Successful save cache')
            except Exception as ex:
                logger.error('Save cache error')
                logger.error('Thread save cache error')
                logger.exception(ex)
                self.bot.send_message('Ошибка при сохранение кэша!\nОбратитесь к администратору и сделайте дамп кэша!')

            try:
                t2 = self.blacklist_items.copy()
                text = ''
                for i in t2:
                    self.blacklist_items.pop(0)
                    text += i + '\n'
                with open('./items/blacklist.txt', 'a', encoding='utf-8') as file:
                    file.write(text)
                logger.success('Successful blacklist items')
            except Exception as ex:
                logger.error('Save blacklist error')
                logger.error('Thread save cache error')
                logger.exception(ex)
                self.bot.send_message('Ошибка при сохранение предметов в черном списке!\nОбратитесь к администратору и сделайте дамп кэша!')

            try:
                t3 = {'notification': future['notification'].copy(), 'autobuy': future['autobuy'].copy()}
                with open('./items/future.json', 'w', encoding='utf-8') as file:
                    json.dump(t3, file, indent=4, ensure_ascii=False)
                logger.success('Successful future items')
            except Exception as ex:
                logger.error('Save future error')
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
                            logger.success('URL PARSING get new BD')
                            raw_tf2_bd = r.text.split('\n')[1:-1]
                            tf2_db = csv.reader(raw_tf2_bd, delimiter=';')
                            for item in tf2_db:
                                classid = item[0]
                                instanceid = item[1]
                                craft = 'Craftable' if item[8] == "1" else 'Non-Craftable'
                                create_logger_item(f'{classid}-{instanceid}')
                                price = float(item[2]) / 100
                                name = item[13]
                                logger.success(f'URL PARSING NEW ITEM {classid}-{instanceid} {name}', id=f'{classid}-{instanceid}')

                                flag = False
                                priority = False
                                flag_autobuy = False
                                if f"{classid}-{instanceid}" not in future['autobuy']:
                                    logger.info(f'URL PARSING {classid}-{instanceid} not in future', id=f'{classid}-{instanceid}')
                                    if f"{classid}-{instanceid}" not in items_cache:
                                        logger.info(f'URL PARSING {classid}-{instanceid} not in cache', id=f'{classid}-{instanceid}')
                                        if name in items_bd_list:
                                            logger.info(f'URL PARSING {classid}-{instanceid} in items bd', id=f'{classid}-{instanceid}')
                                            if craft in items_bd[name]:
                                                logger.info(f'URL PARSING {classid}-{instanceid} {craft} in item bd', id=f'{classid}-{instanceid}')
                                                min_price = items_bd[name][craft]['price'] * config['currency'][items_bd[name][craft]['currency']]
                                                finily_price = 0
                                                filter_price_log = 0
                                                for filter_price in config['filter']['autobuy']:
                                                    if finily_price:
                                                        break
                                                    if filter_price == list(config['filter']['autobuy'])[-1]:
                                                        filter_price_log = filter_price
                                                        finily_price = min_price * ((100 - config['filter']['autobuy'][filter_price]) / 100)
                                                    elif min_price <= float(filter_price):
                                                        filter_price_log = filter_price
                                                        finily_price = min_price * ((100 - config['filter']['autobuy'][filter_price]) / 100)
                                                logger.info(f'URL PARSING {classid}-{instanceid} find filter price: {filter_price_log} Procent filter: {config["filter"]["autobuy"][filter_price_log]} New price: {finily_price} BD price: {min_price} Price item: {price}', id=f'{classid}-{instanceid}')
                                                if price <= finily_price:
                                                    logger.success(f'URL PARSING {classid}-{instanceid} filter autobuy item Price TM: {price} Price DB: {min_price}', id=f'{classid}-{instanceid}')
                                                    flag_autobuy = True
                                                    description = (f'Цена в базе: {min_price}\n'
                                                                   f'Фильтр: {filter_price_log}\n'
                                                                   f'Процент: {config["filter"]["autobuy"][filter_price_log]} %\n'
                                                                   f'Цена в базе с фильтром: {finily_price}\n')
                                                    self.buy_item(classid, instanceid, price, description, name)
                                            else:
                                                logger.info(f'URL PARSING {classid}-{instanceid} {craft} not in item bd', id=f'{classid}-{instanceid}')
                                        else:
                                            logger.info(f'URL PARSING {classid}-{instanceid} not in items bd', id=f'{classid}-{instanceid}')
                                        if not flag_autobuy:
                                            if f"{classid}-{instanceid}" not in future['notification']:
                                                logger.info(f'URL PARSING {classid}-{instanceid} not future notification', id=f'{classid}-{instanceid}')
                                                flag = True
                                            elif price * 100 <= future['notification'][f"{classid}-{instanceid}"]['procent'] and price * 100 != future['notification'][f"{classid}-{instanceid}"]['old_price']:
                                                logger.success(f'URL PARSING {classid}-{instanceid} future notification allow all requirement', id=f'{classid}-{instanceid}')
                                                priority = True
                                                flag = True
                                                future['notification'].pop(f"{classid}-{instanceid}")
                                            else:
                                                old_price = future['notification'][f"{classid}-{instanceid}"]['old_price']
                                                procent = future['notification'][f"{classid}-{instanceid}"]['procent']
                                                logger.warning(f'URL PARSING {classid}-{instanceid} in future notification and price not changing! New price: {price * 100} Old price: {old_price} Need price: {procent}', id=f'{classid}-{instanceid}')
                                    else:
                                        logger.info(f'URL PARSING {classid}-{instanceid} in cache', id=f'{classid}-{instanceid}')
                                elif price * 100 <= future['autobuy'][f"{classid}-{instanceid}"]['procent'] and price * 100 != future['autobuy'][f"{classid}-{instanceid}"]['old_price']:
                                    logger.success(f'URL PARSING {classid}-{instanceid} future autobuy allow all requirement', id=f'{classid}-{instanceid}')
                                    description = (f'Покупка по ПНБ!\n'
                                                   f'Старая цена: {round(future["autobuy"][f"{classid}-{instanceid}"]["old_price"] / 100, 2)}')
                                    future['autobuy'].pop(f"{classid}-{instanceid}")
                                    self.buy_item(classid, instanceid, price, description, name)
                                else:
                                    old_price = future['autobuy'][f"{classid}-{instanceid}"]['old_price']
                                    procent = future['autobuy'][f"{classid}-{instanceid}"]['procent']
                                    logger.warning(f'URL PARSING {classid}-{instanceid} in future autobuy and price not changing! New price: {price * 100} Old price: {old_price} Need price: {procent}', id=f'{classid}-{instanceid}')


                                if flag or flag_autobuy:
                                    logger.success(f'URL PARSING {classid}-{instanceid} next step proccesing items Priority: {priority}', id=f'{classid}-{instanceid}')
                                    items_cache[f"{classid}-{instanceid}"] = {'name': name}
                                    self.count_items_url += 1
                                    self.count_items_cache += 1
                                    self.last_item_url = {'name': name, 'id': f"{classid}-{instanceid}",'date': datetime.datetime.now()}
                                    self.items_queue.put({'name': name, 'classid': classid, 'instanceid': instanceid, 'priority': priority})
                                    delete_logger_item(f'{classid}-{instanceid}')
                                else:
                                    logger.warning(f'URL PARSING {classid}-{instanceid} not go next step Flag: {flag} Flag AB: {flag_autobuy} Priority: {priority}', id=f'{classid}-{instanceid}')
                                    delete_logger_item(f'{classid}-{instanceid}')
                        else:
                            logger.error(f'URL PARSING ERROR status code {r.status_code}')
                else:
                    logger.error(f'URL PARSING ERROR status code {r.status_code}')
            except Exception as ex:
                logger.exception(f'URL {ex}')
            time.sleep(10)
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
                        create_logger_item(f'{classid}-{instanceid}')
                        price = res['ui_price']
                        logger.success(f'WEBSOKCET NEW ITEM {classid}-{instanceid} {name}', id=f'{classid}-{instanceid}')

                        flag = False
                        priority = False
                        flag_autobuy = False
                        if f"{classid}-{instanceid}" not in future['autobuy']:
                            logger.info(f'WEBSOCKET {classid}-{instanceid} not in future', id=f'{classid}-{instanceid}')
                            if f"{classid}-{instanceid}" not in items_cache:
                                logger.info(f'WEBSOCKET {classid}-{instanceid} not in cache', id=f'{classid}-{instanceid}')
                                if name in items_bd_list:
                                    logger.info(f'WEBSOCKET {classid}-{instanceid} in items bd', id=f'{classid}-{instanceid}')
                                    min_price = 99999999999
                                    for craft in items_bd[name]:
                                        min_price = min(items_bd[name][craft]['price'] * config['currency'][items_bd[name][craft]['currency']], min_price)
                                    finily_price = 0
                                    filter_price_log = 0
                                    for filter_price in config['filter']['autobuy']:
                                        if finily_price:
                                            break
                                        if filter_price == list(config['filter']['autobuy'])[-1]:
                                            finily_price = min_price * ((100 - config['filter']['autobuy'][filter_price]) / 100)
                                            filter_price_log = filter_price
                                        elif min_price <= float(filter_price):
                                            finily_price = min_price * ((100 - config['filter']['autobuy'][filter_price]) / 100)
                                            filter_price_log = filter_price
                                    logger.info(f'WEBSOCKET {classid}-{instanceid} find filter price: {filter_price_log} Procent filter: {config["filter"]["autobuy"][filter_price_log]} New price: {finily_price} BD price: {min_price} Price item: {price}', id=f'{classid}-{instanceid}')
                                    if price <= finily_price:
                                        logger.success(f'WEBSOCKET {classid}-{instanceid} filter autobuy item Price TM: {price} Price DB: {min_price}', id=f'{classid}-{instanceid}')
                                        flag_autobuy = True
                                        description = (f'Цена в базе: {min_price}\n'
                                                       f'Фильтр: {filter_price_log}\n'
                                                       f'Процент: {config["filter"]["autobuy"][filter_price_log]} %\n'
                                                       f'Цена в базе с фильтром: {finily_price}\n')
                                        self.buy_item(classid, instanceid, price, description, name)

                                else:
                                    logger.info(f'WEBSOCKET {classid}-{instanceid} not in items bd', id=f'{classid}-{instanceid}')
                                if not flag_autobuy:
                                    if f"{classid}-{instanceid}" not in future['notification']:
                                        logger.info(f'WEBSOCKET {classid}-{instanceid} not future notification', id=f'{classid}-{instanceid}')
                                        flag = True
                                    elif price * 100 <= future['notification'][f"{classid}-{instanceid}"]['procent'] and price * 100 != future['notification'][f"{classid}-{instanceid}"]['old_price']:
                                        logger.success(f'WEBSOCKET {classid}-{instanceid} future notification allow all requirement', id=f'{classid}-{instanceid}')
                                        priority = True
                                        flag = True
                                        future['notification'].pop(f"{classid}-{instanceid}")
                                    else:
                                        old_price = future['notification'][f"{classid}-{instanceid}"]['old_price']
                                        procent = future['notification'][f"{classid}-{instanceid}"]['procent']
                                        logger.warning(f'WEBSOCKET {classid}-{instanceid} in future notification and price not changing! New price: {price * 100} Old price: {old_price} Need price: {procent}', id=f'{classid}-{instanceid}')
                            else:
                                logger.info(f'WEBSOCKET {classid}-{instanceid} in cache', id=f'{classid}-{instanceid}')
                        elif price * 100 <= future['autobuy'][f"{classid}-{instanceid}"]['procent'] and price * 100 != future['autobuy'][f"{classid}-{instanceid}"]['old_price']:
                            logger.success(f'WEBSOCKET {classid}-{instanceid} future autobuy allow all requirement', id=f'{classid}-{instanceid}')
                            description = (f'Покупка по ПНБ!\n'
                                           f'Старая цена: {round(future["autobuy"][f"{classid}-{instanceid}"]["old_price"] / 100, 2)}')
                            future['autobuy'].pop(f"{classid}-{instanceid}")
                            self.buy_item(classid, instanceid, price, description, name)
                        else:
                            old_price = future['autobuy'][f"{classid}-{instanceid}"]['old_price']
                            procent = future['autobuy'][f"{classid}-{instanceid}"]['procent']
                            logger.warning(f'WEBSOCKET {classid}-{instanceid} in future autobuy and price not changing! New price: {price * 100} Old price: {old_price} Need price: {procent}', id=f'{classid}-{instanceid}')

                        if flag or flag_autobuy:
                            logger.success(f'WEBSOCKET {classid}-{instanceid} next step proccesing items Priority: {priority}', id=f'{classid}-{instanceid}')
                            items_cache[f"{classid}-{instanceid}"] = {'name': name}
                            self.count_items_websocket += 1
                            self.count_items_cache += 1
                            self.last_item_websocket = {'name': name, 'id': f"{classid}-{instanceid}", 'date': datetime.datetime.now()}
                            self.items_queue.put({'name': name, 'classid': classid, 'instanceid': instanceid, 'priority': priority})
                        else:
                            logger.warning(f'WEBSOCKET {classid}-{instanceid} not go next step Flag: {flag} Flag AB: {flag_autobuy} Priority: {priority}', id=f'{classid}-{instanceid}')
                            delete_logger_item(f'{classid}-{instanceid}')

            except Exception as ex:
                logger.exception(f'WEBSOCKET {ex}')
        logger.debug('Stop thread websocket parsing')
        logger.debug('Create new thread websocket parsing')
        self.create_thread_parsing_websocket()