import threading

from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, CallbackQuery
from utils.loging import logger
from utils.config import config
from tg_bot.callbacks_data import menu_page
from parsing import TM_Parsing
from tg_bot.utils import create_button
from utils.loading_data import items_bd_list, items_bd_list_unusual, items_cache

def run(bot: TeleBot, tm: TM_Parsing):
    # Кнопка меню
    @bot.message_handler(commands=['menu'])
    @logger.catch()
    def command_menu(message: Message):
        thread_mes_url = 'Работает' if tm.parsing_thread_url.is_alive() else 'Не работает'
        thread_mes_websocket = 'Работает' if tm.parsing_thread_websocket.is_alive() else 'Не работает'
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
               f'1 metal - {config["currency"]["metal"]} ₽\n\n'
               f'Потоки:\n'
               f'Поток ссылки: {thread_mes_url}\n'
               f'Поток вебсокет: {thread_mes_websocket}\n\n'
               f'Кол-во активных потоков: {threading.active_count()}\n'
               f'Кол-во неотправленых сообщений: {tm.bot.count_message_not}')
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
        markup.add(buttons[4])
        bot.send_message(message.chat.id, mes, reply_markup=markup)

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