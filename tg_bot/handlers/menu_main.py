import json
import threading
import time

from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, CallbackQuery
from utils.loging import logger
from utils.config import config
from tg_bot.callbacks_data import menu_page, settings_menu, iff_settings
from parsing import TM_Parsing
from tg_bot.utils import create_button, cancel
from utils.loading_data import items_bd_list, items_bd_list_unusual, items_cache, future
from telebot.util import antiflood

def run(bot: TeleBot, tm: TM_Parsing):
    # Кнопка меню
    @bot.message_handler(commands=['menu'])
    @logger.catch()
    def command_menu(message: Message, callback: CallbackQuery = None):
        mes = (f'Информация:\n\n'
               f'Кол-во пройденых предметов по ссылкам: {tm.count_items_url}\n'
               f'Кол-во пройденых предметов по вебсокету: {tm.count_items_websocket}\n\n'
               f'Последний предмет по ссылкам:\n'
               f'{tm.last_item_url["name"]} {tm.last_item_url["id"]}\n'
               f'Время {tm.last_item_url["date"].strftime("%d/%m %H:%M:%S")}\n\n'
               f'Последний предмет по вебсокету:\n'
               f'{tm.last_item_websocket["name"]} {tm.last_item_websocket["id"]}\n'
               f'Время {tm.last_item_websocket["date"].strftime("%d/%m %H:%M:%S")}\n\n'
               f'Предметов в кэше: {tm.count_items_cache}\n\n'
               f'Курсы:\n'
               f'1 key - {config["currency"]["keys"]} ₽\n'
               f'1 metal - {config["currency"]["metal"]} ₽')
        markup = InlineKeyboardMarkup()
        buttons = [create_button('Проверить предмет', menu_page.new('check_id')),  # 0
                   create_button('Открыть базу', menu_page.new('base')),  # 1
                   create_button('Удалить предмет', menu_page.new('delete_item')),  # 2
                   create_button('Меню автобая', menu_page.new('autobuy_menu')),  # 3
                   create_button('Очистить кэш', menu_page.new('clear_cache')),  # 4
                   create_button('Настройки', menu_page.new('settings')),  # 5
                   create_button('Список ПНБ', menu_page.new('iff'))]  # 6
        markup.add(buttons[3], buttons[1])
        markup.add(buttons[0], buttons[2])
        markup.add(buttons[6], buttons[5])
        #markup.add(buttons[4])
        if callback:
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)
        else:
            bot.send_message(message.chat.id, mes, reply_markup=markup)

    @bot.callback_query_handler(func= lambda x: menu_page.filter(page='iff').check(x))
    @logger.catch()
    def items_for_future(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = menu_page.parse(callback.data)
        markup = InlineKeyboardMarkup()
        markup.add(*[create_button('Уведомления', iff_settings.new(page='list', type='not', page_num=0)),
                     create_button('Автопокупка', iff_settings.new(page='list', type='abuy', page_num=0))])
        markup.add(create_button('Вернуться в меню', menu_page.new(page='menu')))
        mes = f'На данный момент предметов в ПНБ:\n\nУведомления: {len(list(future["notification"]))} шт.\nАвтопокупка: {len(list(future["autobuy"]))} шт.'
        bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func= lambda x: iff_settings.filter().check(x))
    @logger.catch()
    def items_for_future_callback(callback: CallbackQuery, items=None, find_text=None):
        if callback.id != -1:
            bot.answer_callback_query(callback.id)
        data = iff_settings.parse(callback.data)
        if data['page'] == 'list':
            page = int(data['page_num'])
            mes = ''
            if data['type'] == 'not':
                typ = 'notification'
                mes += 'Список предметов ПНБ для уведомлений:\n'
                word = 'прислан'
            elif data['type'] == 'abuy':
                mes += 'Список предметов ПНБ для покупки:\n'
                typ = 'autobuy'
                word = 'куплен'
            buttons = []
            list_items = list(future[typ])
            if not find_text:
                items = list_items.copy()
            if find_text:
                mes = (f'Результат поиска по {find_text}\n'
                       f'Найдено {len(items)} шт.\n\n') + mes

            for i in range(10 * page, 10 * (page + 1)):
                if i < len(items):
                    mes += (f"\n{i + 1}. <a href='https://tf2.tm/en/item/{items[i]}'>{items[i]}</a>\n"
                            f'Название предмета: {future[typ][items[i]]["name"]}\n'
                            f'Старая цена: {round(future[typ][items[i]]["old_price"] / 100, 2)}\n'
                            f'Будет {word} когда цена будет ниже или равно: {round(future[typ][items[i]]["procent"] / 100, 2)}\n')
                    buttons.append(create_button(f'{i + 1}. {items[i]}',iff_settings.new(page='select', type=data['type'], page_num=list_items.index(items[i]))))
            mes += f'\nСтр. {page + 1} из {len(items) // 10 + 1}'
            markup = InlineKeyboardMarkup()
            markup.add(*buttons)
            markup.add(create_button('Найти по айди', iff_settings.new(page='find', type=data['type'], page_num=0)))
            navigation_buttons = []
            if page != 0:
                navigation_buttons.append(create_button('Предыдущая страница', iff_settings.new(page='list', type=data['type'], page_num=page - 1)))
            if page != (len(items) // 10):
                navigation_buttons.append(
                    create_button('Следующая страница', iff_settings.new(page='list', type=data['type'], page_num=page + 1)))
            markup.add(*navigation_buttons)
            markup.add(create_button('Вернуться в меню', menu_page.new(page='iff')))
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup, parse_mode='HTML')
        elif data['page'] == 'select':
            if data['type'] == 'not':
                typ = 'notification'
                word = 'прислан'
            elif data['type'] == 'abuy':
                typ = 'autobuy'
                word = 'куплен'
            list_items = list(future[typ])
            item_num = int(data['page_num'])
            item_future = future[typ][list_items[item_num]]
            mes = (f"<a href='https://tf2.tm/en/item/{list_items[item_num]}'>{list_items[item_num]}</a>\n"
                   f'Название предмета: {item_future["name"]}\n'
                   f'Старая цена: {round(item_future["old_price"] / 100, 2)}\n'
                   f'Будет {word} когда цена будет ниже или равно: {round(item_future["procent"] / 100, 2)}\n')
            markup = InlineKeyboardMarkup()
            markup.add(
                *[create_button('Изменить ценик ПНБ', iff_settings.new(page='edit_price', type=data['type'], page_num=item_num)),
                  create_button('Удалить предмет из ПНБ', iff_settings.new(page='del_item', type=data['type'], page_num=item_num))])
            markup.add(create_button('Вернуться в меню', iff_settings.new(page='list', type=data['type'], page_num=0)))
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup, parse_mode='HTML')
        elif data['page'] == 'edit_price':
            if data['type'] == 'not':
                typ = 'notification'
                word = 'прислан'
            elif data['type'] == 'abuy':
                typ = 'autobuy'
                word = 'куплен'
            mes = f'Пришлите новый ценик когда будет {word} предмет (0 для отмены):'
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, item_for_future_message,  callback, typ, items, 'edit', find_text)
        elif data['page'] == 'del_item':
            mes = 'Вы уверены?'
            markup = InlineKeyboardMarkup()
            markup.add(*[create_button('Да', iff_settings.new(page='sure', type=data['type'], page_num=data['page_num'])),
                         create_button('Нет', iff_settings.new(page='select', type=data['type'], page_num=data['page_num']))])
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)
        elif data['page'] == 'sure':
            if data['type'] == 'not':
                typ = 'notification'
            elif data['type'] == 'abuy':
                typ = 'autobuy'
            list_items = list(future[typ])
            item_num = int(data['page_num'])
            future[typ].pop(list_items[item_num])
            data.pop('@')
            data['page'] = 'list'
            data['page_num'] = 0
            callback.data = iff_settings.new(**data)
            callback.id = -1
            items_for_future_callback(callback)
        elif data['page'] == 'find':
            if data['type'] == 'not':
                typ = 'notification'
            elif data['type'] == 'abuy':
                typ = 'autobuy'
            mes = 'Пришлите полный айди или частичный (0 для отмены):'
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, item_for_future_message,  callback, typ, items, 'find', find_text)
    @logger.catch()
    def item_for_future_message(message: Message, callback: CallbackQuery, typ, items, page, find_text):
        data = iff_settings.parse(callback.data)
        if message.text == '0':
            cancel(bot, message.chat.id)
            data.pop('@')
            if page == 'find':
                data['page'] = 'list'
                data['page_num'] = 0
            elif page == 'edit':
                data['page'] = 'select'
            callback.data = iff_settings.new(**data)
            callback.id = -1
            callback.message = bot.send_message(message.chat.id, 'Пум...')
            items_for_future_callback(callback)
        elif page == 'find':
            text = message.text
            list_items = list(future[typ])
            items_list = []
            for ids in list_items:
                if text in ids:
                    items_list.append(ids)
            data.pop('@')
            data['page'] = 'list'
            callback.data = iff_settings.new(**data)
            callback.id = -1
            callback.message = bot.send_message(message.chat.id, 'Пум...')
            items_for_future_callback(callback, items_list, text)
        elif page == 'edit':
            try:
                price = float(message.text)
                list_items = list(future[typ])
                item_num = int(data['page_num'])
                future[typ][list_items[item_num]]['procent'] = price * 100
                data.pop('@')
                data['page'] = 'select'
                callback.data = iff_settings.new(**data)
                callback.id = -1
                callback.message = bot.send_message(message.chat.id, 'Пум...')
                items_for_future_callback(callback, items, find_text)
            except:
                if typ == 'notification':
                    word = 'прислан'
                elif typ == 'autobuy':
                    word = 'куплен'
                bot.send_message(message.chat.id, 'Неправильный формат!')
                bot.send_message(message.chat.id, f'Пришлите новый ценик когда будет {word} предмет (0 для отмены):')
                bot.register_next_step_handler(callback.message, item_for_future_message,  callback, typ, items, page, find_text)

    # Кнопка открыть базу
    @bot.callback_query_handler(func=lambda x: menu_page.filter(page='base').check(x))
    @logger.catch()
    def menu_base(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        count_not_unusual_items = len(items_bd_list)
        count_unusual_items = len(items_bd_list_unusual)
        count_all_items = count_unusual_items + count_not_unusual_items
        mes = (f"Кол-во предметов: {count_not_unusual_items} шт.\n"
               f"Кол-во unusual предметов: {count_unusual_items} шт.\n\n"
               f"Всего предметов: {count_all_items} шт.")
        markup = InlineKeyboardMarkup()
        buttons = [create_button('Добавить предмет', menu_page.new(page='add_item')),
                   create_button('Найти предмет', menu_page.new(page='find_item'))]
        markup.add(*buttons)
        markup.add(create_button('Вернуться в меню', menu_page.new(page='menu')))
        bot.edit_message_text(text=mes, chat_id=callback.message.chat.id, message_id=callback.message.message_id, reply_markup=markup)

    # Кнопка проверить айди
    @bot.callback_query_handler(func=lambda x: menu_page.filter(page='check_id').check(x))
    @logger.catch()
    def check_item_part_one(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        bot.edit_message_text('Пришлите айди предмета ( 12345-12345 ):', callback.message.chat.id, callback.message.message_id)
        bot.register_next_step_handler(callback.message, check_item)

    @logger.catch()
    def check_item(message: Message):
        text = message.text.strip()
        try:
            if len(text.split('-')) == 2:
                if text in items_cache:
                    bot.send_message(message.chat.id, f'Предмет {text} найден!\nНазвание предмета: {items_cache[text]["name"]}')
                else:
                    bot.send_message(message.chat.id, f'Предмет {text} не найден!')
            else:
                bot.send_message(message.chat.id, f'Неправильный формат!')
        except:
            bot.send_message(message.chat.id, f'Неправильный формат!')

    # Удалить предмет
    @bot.callback_query_handler(func=lambda x: menu_page.filter(page='delete_item').check(x))
    @logger.catch()
    def del_item_part_one(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        bot.edit_message_text('Пришлите айди предмета ( 12345-12345 ):', callback.message.chat.id,
                              callback.message.message_id)
        bot.register_next_step_handler(callback.message, del_item)

    @logger.catch()
    def del_item(message: Message):
        text = message.text.strip()
        try:
            if len(text.split('-')) == 2:
                if text in items_cache:
                    item = items_cache.pop(text)
                    bot.send_message(message.chat.id, f'Предмет {text} успешно удален!\nНазвание предмета: {item["name"]}')
                else:
                    bot.send_message(message.chat.id, f'Предмет {text} не найден!')
            else:
                bot.send_message(message.chat.id, f'Неправильный формат!')
        except:
            bot.send_message(message.chat.id, f'Неправильный формат!')

    @bot.callback_query_handler(func=lambda x: menu_page.filter(page='menu').check(x))
    @logger.catch()
    def menu_callback(callback: CallbackQuery):
        command_menu(callback.message, callback)


    @bot.callback_query_handler(func=lambda x: menu_page.filter(page='settings').check(x))
    @logger.catch()
    def menu_settings(callback: CallbackQuery, mess=False):
        bot.answer_callback_query(callback.id)
        thread_mes_url = 'Работает' if tm.parsing_thread_url.is_alive() else 'Не работает'
        thread_mes_websocket = 'Работает' if tm.parsing_thread_websocket.is_alive() else 'Не работает'
        thread_proccesing = 'Работает' if tm.parsing_thread_processing_items.is_alive() else 'Не работает'
        thread_save_cache = 'Работает' if tm.thread_save_cache.is_alive() else 'Не работает'
        thread_pool_message = 'Работает' if tm.bot.thread_pool.is_alive() else 'Не работает'
        filter_notification_mes = "".join(x + "₽ - " + str(config["filter"]["notification"][x]) + "%\n" for x in config["filter"]["notification"])
        filter_autobuy_mes = "".join(x + "₽ - " + str(config["filter"]["autobuy"][x]) + "%\n" for x in config["filter"]["autobuy"])
        mes = (f'Потоки:\n'
               f'Поток ссылки: {thread_mes_url}\n'
               f'Поток вебсокет: {thread_mes_websocket}\n'
               f'Поток обработки: {thread_proccesing}\n'
               f'Поток сохранение кэша: {thread_save_cache}\n'
               f'Поток пула сообщений: {thread_pool_message}\n\n'
               f'Кол-во айтемов в очереди для потоков: {tm.items_queue.qsize()}\n'
               f'Кол-во активных потоков: {threading.active_count()}\n'
               f'Кол-во неотправленых сообщений: {tm.bot.count_message_not}\n\n'
               f'Черный список: {"".join(i + ", " for i in config["blacklist"])[:-2]}\n\n'
               f'Фильтр:\n'
               f'Уведомления:\n'
               f'{filter_notification_mes}\n'
               f'Автопокупка:\n'
               f'{filter_autobuy_mes}\n'
               f'Курсы:\n'
               f'1 key - {config["currency"]["keys"]} ₽\n'
               f'1 metal - {config["currency"]["metal"]} ₽')
        buttons = [create_button('Перезагрузить потоки парсинга', settings_menu.new(type='reload', dump='parsing')),
                   create_button('Перезагрузить все потоки', settings_menu.new(type='reload', dump='threads')),
                   create_button('Изменить курс', settings_menu.new(type='edit_currency', dump='')),
                   create_button('Изменить черный список', settings_menu.new(type='edit_black', dump='')),
                   create_button('Изменить фильтр', settings_menu.new(type='edit_filter', dump='')),
                   create_button('Выгрузить предметы из ЧС', settings_menu.new(type='dump', dump='blacklist_items')),
                   create_button('Выгрузить базу данных', settings_menu.new(type='dump', dump='db')),
                   create_button('Выгрузить кэш', settings_menu.new(type='dump', dump='cache')),
                   create_button('Выгрузить ПНБ', settings_menu.new(type='dump', dump='iff')),
                   create_button('Очистить кэш', settings_menu.new(type='clear_cache', dump='')),
                   create_button('Вернуться в меню', menu_page.new(page='menu'))]
        markup = InlineKeyboardMarkup()
        markup.add(*buttons, row_width=1)
        if mess:
            bot.send_message(callback.message.chat.id, mes, reply_markup=markup)
        else:
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda x: settings_menu.filter(type='dump').check(x))
    @logger.catch()
    def dump_file(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = settings_menu.parse(callback.data)
        bot.edit_message_text('Подождите', callback.message.chat.id, callback.message.message_id)
        file = ''
        if data['dump'] == 'blacklist_items':
            file = open('./items/blacklist.txt', 'rb')
        elif data['dump'] == 'db':
            file = open('./items/items.json')
            unusual = open('./items/unusual_items.json')
            bot.send_document(callback.message.chat.id, file)
            bot.send_document(callback.message.chat.id, unusual)
            bot.delete_message(callback.message.chat.id, callback.message.message_id)
            bot.send_message(callback.message.chat.id, 'Готово!')
            return 0
        elif data['dump'] == 'cache':
            file = open('./items/cache.json')
        elif data['dump'] == 'iff':
            file = open('./items/future.json')
        if file:
            bot.send_document(callback.message.chat.id, file)
            bot.delete_message(callback.message.chat.id, callback.message.message_id)
            bot.send_message(callback.message.chat.id, 'Готово!')

    @bot.callback_query_handler(func=lambda x: settings_menu.filter(type='reload').check(x))
    @logger.catch()
    def reload(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = settings_menu.parse(callback.data)
        threads = {}
        if data['dump'] == 'parsing':
            threads['Thread URL'] = {'thread': tm.parsing_thread_url, 'status': 'parsing_status_url', 'start': tm.start_thread_parsing_url}
            threads['Thread Websocket'] = {'thread': tm.parsing_thread_websocket, 'status': 'parsing_status_websocket', 'start': tm.start_thread_parsing_websocket}
        elif data['dump'] == 'threads':
            threads['Thread URL'] = {'thread': tm.parsing_thread_url, 'status': 'parsing_status_url', 'start': tm.start_thread_parsing_url}
            threads['Thread Websocket'] = {'thread': tm.parsing_thread_websocket, 'status': 'parsing_status_websocket', 'start': tm.start_thread_parsing_websocket}
            threads['Thread proccesing items'] = {'thread': tm.parsing_thread_processing_items, 'status': 'parsing_status_processing_items', 'start': tm.start_thread_processing}
            threads['Thread save cache'] = {'thread': tm.thread_save_cache, 'status': 'status_save_cache', 'start': tm.start_thread_save_cache}
            threads['Thread pool message'] = {'thread': tm.bot.thread_pool, 'status': 'status_pool', 'start': tm.bot.start_thread_pool}
        mes = f'Статус перезагрузки:\n{"".join(i + " - " + ("✅" if threads[i]["status"] == "true" else "❌") + "!" for i in threads)}'.replace('!', '\n')
        bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id)
        wait_message = bot.send_message(callback.message.chat.id, "Подождите")
        for i in threads:
            if threads[i]['thread'].is_alive():
                if i == 'Thread pool message':
                    setattr(tm.bot, threads[i]['status'], False)
                else:
                    setattr(tm, threads[i]['status'], False)
                threads[i]['thread'].join()
                threads[i]['status'] = 'true'
                time.sleep(1)
                threads[i]['start']()
                mes = f'Статус перезагрузки:\n{"".join(i + " - " + ("✅" if threads[i]["status"] == "true" else "❌") + "!" for i in threads)}'.replace(
                    '!', '\n')
                antiflood(bot.edit_message_text, **{'text': mes, 'chat_id': callback.message.chat.id, 'message_id': callback.message.message_id})
            else:
                threads[i]['status'] = 'true'
                threads[i]['start']()
                mes = f'Статус перезагрузки:\n{"".join(i + " - " + ("✅" if threads[i]["status"] == "true" else "❌") + "!" for i in threads)}'.replace(
                    '!', '\n')
                antiflood(bot.edit_message_text, **{'text': mes, 'chat_id': callback.message.chat.id, 'message_id': callback.message.message_id})
        bot.delete_message(wait_message.chat.id, wait_message.message_id)
        bot.send_message(wait_message.chat.id, 'Все потоки перезагружены!')

    @bot.callback_query_handler(func=lambda x: settings_menu.filter(type='edit_currency').check(x))
    @logger.catch()
    def edit_currency(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = settings_menu.parse(callback.data)
        if data['dump'] == '':
            markup = InlineKeyboardMarkup()
            markup.add(*[create_button('Keys', settings_menu.new(type='edit_currency', dump='keys')),
                         create_button('Metal', settings_menu.new(type='edit_currency', dump='metal'))])
            markup.add(create_button('Отмена', settings_menu.new(type='edit_currency', dump='cancel')))
            bot.edit_message_text('Выберите валюту:', callback.message.chat.id, callback.message.message_id, reply_markup=markup)
        if data['dump'] == 'keys' or data['dump'] == 'metal':
            bot.edit_message_text('Пришлите цену в ₽ (0 для отмены):', callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, edit_currency_mes, data['dump'], callback)
        elif data['dump'] == 'cancel':
            cancel(bot, callback.message.chat.id, callback.message)
            callback.data = menu_page.new(page='settings')
            menu_settings(callback)

    @logger.catch()
    def edit_currency_mes(message: Message, curr, callback):
        if message.text == '0':
            cancel(bot, message.chat.id)
            callback.data = menu_page.new(page='settings')
            menu_settings(callback, mess=True)
        else:
            try:
                price = float(message.text)
                config['currency'][curr] = price
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
                bot.send_message(message.chat.id, 'Успешно изменено!')
            except:
                bot.send_message(message.chat.id, 'Неверный формат!')
                bot.send_message(message.chat.id, 'Пришлите цену в ₽ (0 для отмены):')
                bot.register_next_step_handler(message, edit_currency_mes)
                return 0


    @bot.callback_query_handler(func=lambda x: settings_menu.filter(type='edit_black').check(x))
    @logger.catch()
    def edit_black_callback(callback: CallbackQuery):
        if callback.id != -1:
            bot.answer_callback_query(callback.id)
        data = settings_menu.parse(callback.data)
        if data['dump'] == '':
            mes = f'Черный список:\n{"".join(i + ", " for i in config["blacklist"])[:-2]}'
            markup = InlineKeyboardMarkup()
            markup.add(*[create_button('Добавить ключевое слово', settings_menu.new(type='edit_black', dump='add')),
                         create_button('Удалить ключевое слово', settings_menu.new(type='edit_black', dump='del'))])
            markup.add(create_button('Вернуться в меню', menu_page.new(page='settings')))
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)
        elif data['dump'] == 'add':
            bot.edit_message_text('Пришлите ключевое слово (0 для отмены):', callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, edit_black_message, data['dump'] ,callback)
        elif data['dump'] == 'del':
            bot.edit_message_text('Пришлите ключевое слово которое находится в базе:', callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, edit_black_message, data['dump'], callback)


    @logger.catch()
    def edit_black_message(message: Message, data, callback: CallbackQuery):
        if message.text == '0':
            cancel(bot, message.chat.id)
            callback.data = menu_page.new(page='settings')
            menu_settings(callback, mess=True)
        else:
            if data == 'add':
                try:
                    config['blacklist'].append(message.text)
                    with open('./data/config.json', 'w', encoding='utf-8') as file:
                        json.dump(config, file, ensure_ascii=False, indent=4)
                    mes = bot.send_message(message.chat.id, f'Пум..')
                    callback.message = mes
                    callback.data = settings_menu.new(type='edit_black', dump='')
                    callback.id = -1
                    edit_black_callback(callback)
                except Exception as ex:
                    logger.exception(ex)
            elif data == 'del':
                try:
                    config['blacklist'].pop(config['blacklist'].index(message.text))
                    with open('./data/config.json', 'w', encoding='utf-8') as file:
                        json.dump(config, file, ensure_ascii=False, indent=4)
                    mes = bot.send_message(message.chat.id, f'Пум..')
                    callback.message = mes
                    callback.data = settings_menu.new(type='edit_black', dump='')
                    callback.id = -1
                    edit_black_callback(callback)
                except Exception as ex:
                    logger.exception(ex)
                    bot.send_message(message.chat.id, 'Ошибка при удаленние ключевого слова!')
                    mes = bot.send_message(message.chat.id, f'Пум..')
                    callback.message = mes
                    callback.data = settings_menu.new(type='edit_black', dump='')
                    callback.id = -1
                    edit_black_callback(callback)

    @bot.callback_query_handler(func=lambda x: settings_menu.filter(type='clear_cache').check(x))
    @logger.catch()
    def clear_cache(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = settings_menu.parse(callback.data)
        if data['dump'] == '':
            markup = InlineKeyboardMarkup()
            markup.add(*[create_button('Да', settings_menu.new(type='clear_cache', dump='yes')),
                         create_button('Нет', menu_page.new(page='settings'))])
            markup.add(create_button('Вернуться в меню', menu_page.new(page='settings')))
            bot.edit_message_text('Вы уверены?', callback.message.chat.id, callback.message.message_id, reply_markup=markup)
        elif data['dump'] == 'yes':
            keys = items_cache.copy()
            for i in keys:
                items_cache.pop(i)
            tm.count_items_cache = 0
            bot.edit_message_text('Кэш успешно удален!', callback.message.chat.id, callback.message.message_id)


    @bot.callback_query_handler(func=lambda x: settings_menu.filter(type='edit_filter').check(x))
    @logger.catch()
    def edit_filter(callback: CallbackQuery):
        if callback.id != -1:
            bot.answer_callback_query(callback.id)
        data = settings_menu.parse(callback.data)
        if data['dump'] == '':
            filter_notification_mes = "".join(x + "₽ - " + str(config["filter"]["notification"][x]) + "%\n" for x in config["filter"]["notification"])
            filter_autobuy_mes = "".join(x + "₽ - " + str(config["filter"]["autobuy"][x]) + "%\n" for x in config["filter"]["autobuy"])
            mes = (f'Фильтр:\n'
               f'Уведомления:\n'
               f'{filter_notification_mes}\n'
               f'Автопокупка:\n'
               f'{filter_autobuy_mes}')
            markup = InlineKeyboardMarkup()
            markup.add(*[create_button('Добавить фильтр', settings_menu.new(type='edit_filter', dump='add')),
                         create_button('Удалить фильтр', settings_menu.new(type='edit_filter', dump='del'))])
            markup.add(create_button('Вернуться в меню', menu_page.new(page='settings')))
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)
        elif data['dump'] == 'add' or data['dump'] == 'del':
            mes = 'Выберите:'
            markup = InlineKeyboardMarkup()
            markup.add(*[create_button('Уведомления', settings_menu.new(type='edit_filter', dump=f"notification_{data['dump']}s")),
                         create_button('Автобай', settings_menu.new(type='edit_filter', dump=f"autobuy_{data['dump']}s"))])
            markup.add(create_button('Вернуться в меню', settings_menu.new(type='edit_filter', dump='')))
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)
        elif 'adds' in data['dump']:
            mes = 'Пришлите до какой суммы нужно установить фильтр (0 для отмены):'
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, edit_filter_mes, data['dump'], 0, callback)
        elif 'dels' in data['dump']:
            ty, trash = data['dump'].split('_')
            mes = 'Выберите который фильтр хотите удалить:'
            markup = InlineKeyboardMarkup()
            markup.add(*[create_button(f'{price}₽ - {config["filter"][ty][price]}%', settings_menu.new(type='edit_filter', dump=f'{ty}_end_{price}')) for price in config['filter'][ty]], row_width=1)
            markup.add(create_button('Вернуться в меню', settings_menu.new(type='edit_filter', dump='')))
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)
        elif 'end' in data['dump']:
            ty, trash, price = data['dump'].split('_')
            config['filter'][ty].pop(price)
            with open('./data/config.json', 'w', encoding='utf-8') as file:
                json.dump(config, file, ensure_ascii=False, indent=4)
            callback.data = settings_menu.new(type='edit_filter', dump='')
            edit_filter(callback)

    @logger.catch()
    def edit_filter_mes(message: Message, type, price, callback):
        if message.text == '0':
            cancel(bot, message.chat.id)
            callback.data = settings_menu.new(type='edit_filter', dump='')
            mes = bot.send_message(message.chat.id, 'Пум..')
            callback.message = mes
            edit_filter(callback)
        elif 'adds' in type:
            try:
                price = int(message.text)
                mes = 'Пришлите процент от 1 до 100 (0 для отмены):'
                ty, trash = type.split('_')
                bot.send_message(message.chat.id, mes)
                bot.register_next_step_handler(message, edit_filter_mes, f'{ty}_end', price, callback)
            except:
                bot.send_message(message.chat.id, 'Неправильный формат!')
                bot.send_message(message.chat.id, 'Пришлите до какой суммы нужно установить фильтр (0 для отмены):')
                bot.register_next_step_handler(callback.message, edit_filter_mes, type, price, callback)
        elif 'end' in type:
            try:
                procent = int(message.text)
                if procent not in [i for i in range(1,101)]:
                    a = 10 / 0
                mes = 'Пум...'
                ty, trash = type.split('_')
                config['filter'][ty][str(price)] = procent
                config['filter'][ty] = dict(sorted(config['filter'][ty].items(), key=lambda item: int(item[0])))
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
                mes = bot.send_message(message.chat.id, mes)
                callback.data = settings_menu.new(type='edit_filter', dump='')
                callback.message = mes
                callback.id = -1
                edit_filter(callback)
            except:
                bot.send_message(message.chat.id, 'Неправильный формат!')
                bot.send_message(message.chat.id, 'Пришлите процент от 1 до 100 (0 для отмены):')
                bot.register_next_step_handler(callback.message, edit_filter_mes, type, price, callback)
