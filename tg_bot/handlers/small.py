import json
import time
from telebot.util import extract_arguments
from telebot import TeleBot
from telebot.types import Message
from parsing import TM_Parsing
from telebot.util import antiflood
from utils import loading_data
from utils.loading_data import items_cache, future, items_bd_list, items_bd
from utils.config import config
from utils.loging import create_logger_item, get_logs
def run(bot: TeleBot, tm: TM_Parsing):
    @bot.message_handler(commands=['stop'])
    def stop(message: Message):
        args = extract_arguments(message.text)
        threads = {}
        threads['Thread URL'] = {'thread': tm.parsing_thread_url, 'status': 'parsing_status_url'}
        threads['Thread Websocket'] = {'thread': tm.parsing_thread_websocket, 'status': 'parsing_status_websocket'}
        threads['Thread proccesing items'] = {'thread': tm.parsing_thread_processing_items, 'status': 'parsing_status_processing_items'}
        threads['Thread save cache'] = {'thread': tm.thread_save_cache, 'status': 'status_save_cache'}
        threads['Thread pool message'] = {'thread': tm.bot.thread_pool, 'status': 'status_pool'}
        mes = f'Статус выключение:\n{"".join(i + " - " + ("✅" if threads[i]["status"] == "true" else "❌") + "!" for i in threads)}'.replace(
            '!', '\n')
        huy = bot.send_message(message.chat.id, mes)
        wait_message = bot.send_message(message.chat.id, "Подождите")
        if not args:
            for i in threads:
                if threads[i]['thread'].is_alive():
                    if i == 'Thread pool message':
                        setattr(tm.bot, threads[i]['status'], False)
                    else:
                        setattr(tm, threads[i]['status'], False)
                    threads[i]['thread'].join()
                    threads[i]['status'] = 'true'
                    mes = f'Статус выключение:\n{"".join(i + " - " + ("✅" if threads[i]["status"] == "true" else "❌") + "!" for i in threads)}'.replace(
                        '!', '\n')
                    antiflood(bot.edit_message_text, **{'text': mes, 'chat_id': huy.chat.id, 'message_id': huy.message_id})
                else:
                    threads[i]['status'] = 'true'
                    mes = f'Статус выключение:\n{"".join(i + " - " + ("✅" if threads[i]["status"] == "true" else "❌") + "!" for i in threads)}'.replace(
                        '!', '\n')
                    antiflood(bot.edit_message_text, **{'text': mes, 'chat_id': huy.chat.id, 'message_id': huy.message_id})
            bot.delete_message(wait_message.chat.id, wait_message.message_id)
            bot.send_message(wait_message.chat.id, 'Все потоки выключены!')
        else:
            if args in threads:
                i = args
                if threads[i]['thread'].is_alive():
                    if i == 'Thread pool message':
                        setattr(tm.bot, threads[i]['status'], False)
                    else:
                        setattr(tm, threads[i]['status'], False)
                    threads[i]['thread'].join()
                    threads[i]['status'] = 'true'
                    mes = f'Статус выключение:\n{"".join(i + " - " + ("✅" if threads[i]["status"] == "true" else "❌") + "!" for i in threads)}'.replace(
                        '!', '\n')
                    antiflood(bot.edit_message_text,
                              **{'text': mes, 'chat_id': huy.chat.id, 'message_id': huy.message_id})
                else:
                    threads[i]['status'] = 'true'
                    mes = f'Статус выключение:\n{"".join(i + " - " + ("✅" if threads[i]["status"] == "true" else "❌") + "!" for i in threads)}'.replace(
                        '!', '\n')
                    antiflood(bot.edit_message_text,
                              **{'text': mes, 'chat_id': huy.chat.id, 'message_id': huy.message_id})
            bot.delete_message(wait_message.chat.id, wait_message.message_id)
            bot.send_message(wait_message.chat.id, f'{i} выключен!')
    @bot.message_handler(commands=['start'])
    def start(message: Message):
        args = extract_arguments(message.text)
        threads = {}
        threads['Thread URL'] = {'start': tm.start_thread_parsing_url}
        threads['Thread Websocket'] = {'start': tm.start_thread_parsing_websocket}
        threads['Thread proccesing items'] = {'start': tm.start_thread_processing}
        threads['Thread save cache'] = {'start': tm.start_thread_save_cache}
        threads['Thread pool message'] = {'start': tm.bot.start_thread_pool}
        if args:
            if args in threads:
                threads[args]['start']()
                bot.send_message(message.chat.id, f'{args} Запущен')


    @bot.message_handler(commands=['list'])
    def command_list(message: Message):
        bot.send_message(message.chat.id, 'Thread URL\n'
                                          'Thread Websocket\n'
                                          'Thread proccesing items\n'
                                          'Thread save cache\n'
                                          'Thread pool message')
    @bot.message_handler(commands=['huy'])
    def huy(message: Message):
        with open('./test.json', 'w', encoding='utf-8') as file:
            json.dump(message.json, file, indent=4, ensure_ascii=False)

    @bot.message_handler(commands=['add'])
    def add(message: Message):
        args = extract_arguments(message.text)
        name, url, price = args.split('\n')
        i = 1
        if config['test_get_item']:
            i = int(list(config['test_get_item'])[-1]) + 1
        config['test_get_item'][str(i)] = {'name': name, 'url': url, 'price': price}
        with open('./data/config.json', 'w', encoding='utf-8') as file:
            json.dump(config, file, ensure_ascii=False, indent=4)
        bot.send_message(message.chat.id, 'Добавлено')

    @bot.message_handler(commands=['items'])
    def items_list(message: Message):
        mes = ''
        for i in config['test_get_item']:
            mes += f'{i} {config["test_get_item"][i]["name"]} {config["test_get_item"][i]["price"]}\n'
        bot.send_message(message.chat.id, mes)

    @bot.message_handler(commands=['get'])
    def get(message: Message):
        args = extract_arguments(message.text)
        item = config["test_get_item"][args]

        url = item['url']
        ids = url.split('/')[-1]
        classid, instanceid =  ids.split('-')
        if f'{classid}-{instanceid}' not in tm.status_items:
            tm.status_items[f'{classid}-{instanceid}'] = False
        #create_logger_item(f'{classid}-{instanceid}')
        price = float(item['price'])
        name = item['name']

        flag = False
        priority = False
        flag_autobuy = False
        if f"{classid}-{instanceid}" not in future['autobuy']:
            if f"{classid}-{instanceid}" not in items_cache:
                if name in items_bd_list:
                    min_price = 99999999999
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
                        mes = (f'ТЕСТ!\n'
                               f'Покупаем предмет по фильтру 1 этап обработки\n'
                               f'Название предмета: {name}\n'
                               f'Айди: {classid}-{instanceid}\n'
                               f'Цена тм: {price}\n'
                               f'Цена в базе: {min_price}\n'
                               f'Цена в базе с фильтром: {finily_price}')
                        print(mes + '\n\n')
                if not flag_autobuy:
                    if f"{classid}-{instanceid}" not in future['notification']:
                        flag = True
                    elif price * 100 <= future['notification'][f"{classid}-{instanceid}"]['procent'] and price * 100 != \
                            future['notification'][f"{classid}-{instanceid}"]['old_price']:
                        priority = True
                        flag = True
                        future['notification'].pop(f"{classid}-{instanceid}")
        elif price * 100 <= future['autobuy'][f"{classid}-{instanceid}"]['procent'] and price * 100 != \
                future['autobuy'][f"{classid}-{instanceid}"]['old_price']:
            mes = (f'ТЕСТ!\n'
                   f'Покупаем предмет по ПНБ\n'
                   f'Название предмета: {name}\n'
                   f'Айди: {classid}-{instanceid}\n'
                   f'Цена тм: {price}\n'
                   f'{future["autobuy"][f"{classid}-{instanceid}"]["procent"]}')
            print(mes + '\n\n')
            future['autobuy'].pop(f"{classid}-{instanceid}")

        print(flag)

        if flag or flag_autobuy:
            items_cache[f"{ids}"] = {'name': name}
            tm.items_queue.put({'name': name, 'classid': classid, 'instanceid': instanceid, 'priority': priority})
            bot.send_message(message.chat.id, f'Предмет {name} успешно ушел на проверку!\n{ids}')
        else:
            bot.send_message(message.chat.id, f'Предмет {name} {classid}-{instanceid} есть в кэше!')

    @bot.message_handler(commands=['test'])  # TODO: Command test
    def command_test(message: Message):
        bot.send_message(message.chat.id, f'Chat id: {message.chat.id}\nThread id: {message.message_thread_id}',
                         message_thread_id=message.message_thread_id)

    @bot.message_handler(commands=['saves'])
    def command_saves(message: Message):
        with open('test1.json', 'w', encoding='utf-8') as file:
            json.dump(get_logs(), file, indent=4, ensure_ascii=False)
        with open('test2.json', 'w', encoding='utf-8') as file:
            json.dump(tm.status_items, file, indent=4, ensure_ascii=False)

        with open('test1.json', 'r', encoding='utf-8') as file:
            bot.send_document(message.chat.id, file)
        with open('test2.json', 'r', encoding='utf-8') as file:
            bot.send_document(message.chat.id, file)
            
    @bot.message_handler(commands=['check'])
    def check(message: Message):
        len1 = len(items_cache)
        with open('./items/cache.json', 'r', encoding='utf-8') as file:
            cache_t = json.load(file)
        len2 = len(cache_t)
        mes1 = f'Item Cache: {len1} {len2}'

        len1 = len(future['notification'])
        with open('./items/future.json', 'r', encoding='utf-8') as file:
            future_t = json.load(file)
        len2 = len(future_t['notification'])

        mes2 = f'Notification: {len1} {len2}'

        len1 = len(future['autobuy'])
        len2 = len(future_t['autobuy'])

        mes3 = f'Autobuy: {len1} {len2}'

        mes = f'{mes1}\n{mes2}\n{mes3}'

        bot.send_message(message.chat.id, mes)