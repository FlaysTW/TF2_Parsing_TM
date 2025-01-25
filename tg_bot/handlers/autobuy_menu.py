from telebot import TeleBot
from telebot.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from tg_bot.utils import create_button, cancel
from parsing import TM_Parsing
from telebot.util import antiflood
from tg_bot.callbacks_data import menu_page, settings_menu, iff_settings, autobuy_list
from utils.loging import logger
from utils.config import config
import json

def run(bot: TeleBot, tm: TM_Parsing, bot_parsing: TeleBot):

    @bot.callback_query_handler(func=lambda x: autobuy_list.filter(data='autobuy_spell').check(x) or autobuy_list.filter(data='autobuy_unusual').check(x) or autobuy_list.filter(data='autobuy_all_items').check(x) or autobuy_list.filter(data='menu').check(x))
    @logger.catch()
    def autobuy_menu(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)

        data = autobuy_list.parse(callback.data)
        if data['data'] != 'menu':
            setattr(tm, data['data'], not getattr(tm, data['data']))

        mes = (f'Статусы автопокупки:\n\n'
               f'Spells - {str(tm.autobuy_spell).replace("False", "Отключено").replace("True", "Включено")}\n'
               f'Unusual - {str(tm.autobuy_unusual).replace("False", "Отключено").replace("True", "Включено")}\n'
               f'All items - {str(tm.autobuy_all_items).replace("False", "Отключено").replace("True", "Включено")}')
        markup = InlineKeyboardMarkup()
        markup.add(create_button(f'Spells - {str(tm.autobuy_spell).replace("False", "❌").replace("True", "✅")}',
                                 autobuy_list.new(data='autobuy_spell')))
        markup.add(create_button(f'Unusual - {str(tm.autobuy_unusual).replace("False", "❌").replace("True", "✅")}',
                                 autobuy_list.new(data='autobuy_unusual')))
        markup.add(create_button(f'All items - {str(tm.autobuy_all_items).replace("False", "❌").replace("True", "✅")}',
                                 autobuy_list.new(data='autobuy_all_items')))
        markup.add(create_button('⠀', 'huyhuy'))
        markup.add(create_button('Изменить черный список', autobuy_list.new(data='edit_blacklist')))
        markup.add(create_button('Вернуться в меню', menu_page.new(page='menu')))
        bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func= lambda x: autobuy_list.filter(data='edit_blacklist').check(x))
    @logger.catch()
    def edit_callback_menu(callback: CallbackQuery):
        if callback.id != -1:
            bot.answer_callback_query(callback.id)
        mes = f'Список предметов в черном списке на автопокупку:\n\n{"".join(item + ", " for item in config["autobuy_blacklist"])[:-2]}'
        markup = InlineKeyboardMarkup()
        markup.add(create_button('Добавить', autobuy_list.new(data='autobuy_add')), create_button('Удалить', autobuy_list.new(data='autobuy_del')))
        markup.add(create_button('Вернуться в меню', autobuy_list.new(data='menu')))
        if callback.id == -1:
            bot.send_message(callback.message.chat.id, mes, reply_markup=markup)
        else:
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda x: autobuy_list.filter(data='autobuy_add').check(x) or autobuy_list.filter(data='autobuy_del').check(x))
    @logger.catch()
    def edit_blacklist_callback(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = autobuy_list.parse(callback.data)

        if data['data'] == 'autobuy_add':
            bot.edit_message_text('Пришлите полное название или ключевое слово для добавление (0 для отмены):', callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, edit_blacklist_message, 'autobuy_add', callback)
        elif data['data'] == 'autobuy_del':
            bot.edit_message_text('Пришлите полное название для удаление из ЧС (0 для отмены):', callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, edit_blacklist_message, 'autobuy_del', callback)

    def edit_blacklist_message(message: Message, type_data, callback: CallbackQuery):
        raw_text = message.text
        text = raw_text.lower().strip()
        if text == '0':
            callback.id = -1
            edit_callback_menu(callback)
        elif type_data == 'autobuy_add':
            config['autobuy_blacklist'].append(text)
            with open('./data/config.json', 'w', encoding='utf-8') as file:
                json.dump(config, file, ensure_ascii=False, indent=4)
            callback.id = -1
            edit_callback_menu(callback)
        elif type_data == 'autobuy_del':
            if text in config['autobuy_blacklist']:
                config['autobuy_blacklist'].pop(config['autobuy_blacklist'].index(text))
                callback.id = -1
                edit_callback_menu(callback)
            else:
                markup = InlineKeyboardMarkup()
                markup.add(create_button('Повторить', autobuy_list.new(data='autobuy_del')))
                markup.add(create_button('Вернуться в меню', autobuy_list.new(data='edit_blacklist')))
                bot.send_message(message.chat.id, f'"{raw_text}" нету в черном списке!', reply_markup=markup)

    @bot.callback_query_handler(func= lambda x: x.data == 'huyhuy')
    def void_answer_callback(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)

