import json
import time
from telebot.util import extract_arguments
from telebot import TeleBot
from telebot.types import Message
from parsing import TM_Parsing
from telebot.util import antiflood
from utils import loading_data
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