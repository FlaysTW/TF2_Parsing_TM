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

    @bot.callback_query_handler(func=lambda x: autobuy_list.filter(data='autobuy_1_all_items').check(x) or autobuy_list.filter(data='autobuy_2_all_items').check(x) or autobuy_list.filter(data='menu').check(x))
    @logger.catch()
    def autobuy_menu(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)

        data = autobuy_list.parse(callback.data)
        if data['data'] != 'menu':
            setattr(tm, data['data'], not getattr(tm, data['data']))

        mes = (f'Статусы автопокупки:\n\n'
               f'Spells - {str(tm.autobuy_spell).replace("False", "Отключено").replace("True", "Включено")}\n'
               f'Unusual - {str(tm.autobuy_unusual).replace("False", "Отключено").replace("True", "Включено")}\n'
               f'Paint Color - {str(tm.autobuy_color).replace("False", "Отключено").replace("True", "Включено")}\n'
               f'Scores - {str(tm.autobuy_scores).replace("False", "Отключено").replace("True", "Включено")}\n'
               f'All items 1 step - {str(tm.autobuy_1_all_items).replace("False", "Отключено").replace("True", "Включено")}\n'
               f'All items 2 step - {str(tm.autobuy_2_all_items).replace("False", "Отключено").replace("True", "Включено")}')
        markup = InlineKeyboardMarkup()
        markup.add(create_button(f'All items 1 step - {str(tm.autobuy_1_all_items).replace("False", "❌").replace("True", "✅")}', autobuy_list.new(data='autobuy_1_all_items')))
        markup.add(create_button(f'All items 2 step - {str(tm.autobuy_2_all_items).replace("False", "❌").replace("True", "✅")}', autobuy_list.new(data='autobuy_2_all_items')))
        markup.add(create_button('⠀', 'huyhuy'))
        markup.add(create_button('Изменить настройку Spells', autobuy_list.new(data='edit_spells')))
        markup.add(create_button('Изменить настройку Unusual', autobuy_list.new(data='edit_unusual')))
        markup.add(create_button('Изменить настройку Paint Color', autobuy_list.new(data='edit_color')))
        markup.add(create_button('Изменить настройку Scores', autobuy_list.new(data='edit_scores')))
        markup.add(create_button('Изменить черный список', autobuy_list.new(data='edit_blacklist')))
        markup.add(create_button('Вернуться в меню', menu_page.new(page='menu')))
        bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda x: autobuy_list.filter(data='edit_spells').check(x) or autobuy_list.filter(data='autobuy_spell').check(x))
    @logger.catch()
    def edit_spells_callback_menu(callback: CallbackQuery):
        if callback.id != -1:
            bot.answer_callback_query(callback.id)

        data = autobuy_list.parse(callback.data)
        if data['data'] != 'edit_spells':
            setattr(tm, data['data'], not getattr(tm, data['data']))

        mes = (f'Настройка автопокупки для спеллов:\n\n'
               f'Spells - {str(tm.autobuy_spell).replace("False", "Отключено").replace("True", "Включено")}\n')
        markup = InlineKeyboardMarkup()
        markup.add(create_button('Добавить', autobuy_list.new(data='spells_ab_add')),
                   create_button('Удалить', autobuy_list.new(data='spells_ab_del')))
        markup.add(create_button(f'{str(tm.autobuy_spell).replace("False", "Включить").replace("True", "Выключить")}', autobuy_list.new(data='autobuy_spell')))
        markup.add(create_button('Вернуться в меню', autobuy_list.new(data='menu')))
        if callback.id == -1:
            bot.send_message(callback.message.chat.id, mes, reply_markup=markup)
        else:
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda x: autobuy_list.filter(data='edit_unusual').check(x) or autobuy_list.filter(data='autobuy_unusual').check(x))
    @logger.catch()
    def edit_unusual_callback_menu(callback: CallbackQuery):
        if callback.id != -1:
            bot.answer_callback_query(callback.id)

        data = autobuy_list.parse(callback.data)
        if data['data'] != 'edit_unusual':
            setattr(tm, data['data'], not getattr(tm, data['data']))

        mes = (f'Настройка автопокупки для Unusual:\n\n'
               f'Unusual - {str(tm.autobuy_unusual).replace("False", "Отключено").replace("True", "Включено")}\n')
        markup = InlineKeyboardMarkup()
        markup.add(create_button('Добавить', autobuy_list.new(data='unusual_ab_add')),
                   create_button('Удалить', autobuy_list.new(data='unusual_ab_del')))
        markup.add(create_button(f'{str(tm.autobuy_unusual).replace("False", "Включить").replace("True", "Выключить")}', autobuy_list.new(data='autobuy_unusual')))
        markup.add(create_button('Вернуться в меню', autobuy_list.new(data='menu')))
        if callback.id == -1:
            bot.send_message(callback.message.chat.id, mes, reply_markup=markup)
        else:
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda x: autobuy_list.filter(data='edit_color').check(x) or autobuy_list.filter(data='autobuy_color').check(x))
    @logger.catch()
    def edit_color_callback_menu(callback: CallbackQuery):
        if callback.id != -1:
            bot.answer_callback_query(callback.id)

        data = autobuy_list.parse(callback.data)
        if data['data'] != 'edit_color':
            setattr(tm, data['data'], not getattr(tm, data['data']))

        mes = (f'Настройка автопокупки для Paint color:\n\n'
               f'Paint Color  - {str(tm.autobuy_color).replace("False", "Отключено").replace("True", "Включено")}\n')
        markup = InlineKeyboardMarkup()
        markup.add(create_button('Добавить', autobuy_list.new(data='color_ab_add')),
                   create_button('Удалить', autobuy_list.new(data='color_ab_del')))
        markup.add(create_button('Настройка уведомлений', autobuy_list.new(data='color_notification_edit')))
        markup.add(create_button(f'{str(tm.autobuy_color).replace("False", "Включить").replace("True", "Выключить")}', autobuy_list.new(data='autobuy_color')))
        markup.add(create_button('Вернуться в меню', autobuy_list.new(data='menu')))
        if callback.id == -1:
            bot.send_message(callback.message.chat.id, mes, reply_markup=markup)
        else:
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda x: autobuy_list.filter(data='edit_scores').check(x) or autobuy_list.filter(data='autobuy_scores').check(x))
    @logger.catch()
    def edit_scores_callback_menu(callback: CallbackQuery):
        if callback.id != -1:
            bot.answer_callback_query(callback.id)

        data = autobuy_list.parse(callback.data)
        if data['data'] != 'edit_scores':
            setattr(tm, data['data'], not getattr(tm, data['data']))

        mes = (f'Настройка автопокупки для счетчиков:\n\n'
               f'Scores - {str(tm.autobuy_scores).replace("False", "Отключено").replace("True", "Включено")}\n')
        markup = InlineKeyboardMarkup()
        markup.add(create_button('Добавить', autobuy_list.new(data='scores_ab_add')),
                   create_button('Удалить', autobuy_list.new(data='scores_ab_del')))
        markup.add(create_button('Настройка уведомлений', autobuy_list.new(data='scores_notification_edit')))
        markup.add(create_button(f'{str(tm.autobuy_scores).replace("False", "Включить").replace("True", "Выключить")}', autobuy_list.new(data='autobuy_scores')))
        markup.add(create_button('Вернуться в меню', autobuy_list.new(data='menu')))
        if callback.id == -1:
            bot.send_message(callback.message.chat.id, mes, reply_markup=markup)
        else:
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func= lambda x: autobuy_list.filter(data='edit_blacklist').check(x))
    @logger.catch()
    def edit_blacklist_callback_menu(callback: CallbackQuery):
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
            edit_blacklist_callback_menu(callback)
        elif type_data == 'autobuy_add':
            config['autobuy_blacklist'].append(text)
            with open('./data/config.json', 'w', encoding='utf-8') as file:
                json.dump(config, file, ensure_ascii=False, indent=4)
            callback.id = -1
            edit_blacklist_callback_menu(callback)
        elif type_data == 'autobuy_del':
            if text in config['autobuy_blacklist']:
                config['autobuy_blacklist'].pop(config['autobuy_blacklist'].index(text))
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
                callback.id = -1
                edit_blacklist_callback_menu(callback)
            else:
                markup = InlineKeyboardMarkup()
                markup.add(create_button('Повторить', autobuy_list.new(data='autobuy_del')))
                markup.add(create_button('Вернуться в меню', autobuy_list.new(data='edit_blacklist')))
                bot.send_message(message.chat.id, f'"{raw_text}" нету в черном списке!', reply_markup=markup)

    @bot.callback_query_handler(func= lambda x: x.data == 'huyhuy')
    def void_answer_callback(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)

    @bot.callback_query_handler(func=lambda x: autobuy_list.filter().check(x))
    @logger.catch()
    def huyhuyv2(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        print(callback.data)
