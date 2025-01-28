from telebot import TeleBot
from telebot.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from tg_bot.utils import create_button, cancel
from parsing import TM_Parsing
from telebot.util import antiflood
from tg_bot.callbacks_data import menu_page, settings_menu, iff_settings, autobuy_list, notification_list
from utils.loging import logger
from utils.config import config
import json

def run(bot: TeleBot, tm: TM_Parsing, bot_parsing: TeleBot):

    @bot.callback_query_handler(func=lambda x: autobuy_list.filter(data='autobuy_1_all_items').check(x) or autobuy_list.filter(data='autobuy_2_all_items').check(x) or autobuy_list.filter(data='menu').check(x))
    @logger.catch()
    def autobuy_menu(callback: CallbackQuery):
        if callback.id != -1:
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
               f'All items 2 step - {str(tm.autobuy_2_all_items).replace("False", "Отключено").replace("True", "Включено")}\n\n'
               f'Максимальная цена покупки - {config["autobuy_max_price"]} ₽')
        markup = InlineKeyboardMarkup()
        markup.add(create_button(f'All items 1 step - {str(tm.autobuy_1_all_items).replace("False", "❌").replace("True", "✅")}', autobuy_list.new(data='autobuy_1_all_items')))
        markup.add(create_button(f'All items 2 step - {str(tm.autobuy_2_all_items).replace("False", "❌").replace("True", "✅")}', autobuy_list.new(data='autobuy_2_all_items')))
        markup.add(create_button('⠀', 'huyhuy'))
        markup.add(create_button('Изменить настройку Spells', autobuy_list.new(data='edit_spells')))
        markup.add(create_button('Изменить настройку Unusual', autobuy_list.new(data='edit_unusual')))
        markup.add(create_button('Изменить настройку Paint Color', autobuy_list.new(data='edit_color')))
        markup.add(create_button('Изменить настройку Scores', autobuy_list.new(data='edit_scores')))
        markup.add(create_button('Изменить черный список', autobuy_list.new(data='edit_blacklist')))
        markup.add(create_button('Изменить макс. цену покупки', autobuy_list.new(data='edit_max_price')))
        markup.add(create_button('Вернуться в меню', menu_page.new(page='menu')))
        if callback.id == -1:
            bot.send_message(callback.message.chat.id, mes, reply_markup=markup)
        else:
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda x: autobuy_list.filter(data='edit_max_price').check(x))
    @logger.catch()
    def edit_max_price_callback(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        bot.edit_message_text('Пришлите новую максимальную цену (0 для отмены):', callback.message.chat.id, callback.message.message_id)
        bot.register_next_step_handler(callback.message, edit_max_price_message, callback)

    @logger.catch()
    def edit_max_price_message(message: Message, callback: CallbackQuery):
        raw_text = message.text
        if raw_text == '0':
            callback.id = -1
            autobuy_menu(callback)
        else:
            try:
                price = float(raw_text)
                config['autobuy_max_price'] = price
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
                callback.id = -1
                autobuy_menu(callback)
            except:
                bot.send_message(message.chat.id, 'Неправильный формат!')
                bot.send_message(message.chat.id, 'Пришлите новую максимальную цену (0 для отмены):')
                bot.register_next_step_handler(callback.message, edit_max_price_message, callback)

    @bot.callback_query_handler(func=lambda x: autobuy_list.filter(data='edit_spells').check(x) or autobuy_list.filter(data='autobuy_spell').check(x))
    @logger.catch()
    def edit_spells_callback_menu(callback: CallbackQuery):
        if callback.id != -1:
            bot.answer_callback_query(callback.id)
            data = autobuy_list.parse(callback.data)
            if data['data'] != 'edit_spells':
                setattr(tm, data['data'], not getattr(tm, data['data']))

        help1 = '\n'
        mes = (f'Настройка автопокупки для спеллов:\n\n'
               f'Spells - {str(tm.autobuy_spell).replace("False", "Отключено").replace("True", "Включено")}\n\n'
               f'Название - Покупка - Переплата\n\n'
               f'{"".join(name + "/" + config["autobuy_spells"]["ru"][name]["en"] + f" - " + str(config["autobuy_spells"]["ru"][name]["price"]) + f"₽ - " + str(config["autobuy_spells"]["ru"][name]["over_price"]) + "₽" + help1 for name in config["autobuy_spells"]["ru"])[:-1]}')
        markup = InlineKeyboardMarkup()
        markup.add(create_button('Добавить', autobuy_list.new(data='spells_ab_add')),
                   create_button('Удалить', autobuy_list.new(data='spells_ab_del')))
        markup.add(create_button(f'{str(tm.autobuy_spell).replace("False", "Включить").replace("True", "Выключить")}', autobuy_list.new(data='autobuy_spell')))
        markup.add(create_button('Вернуться в меню', autobuy_list.new(data='menu')))
        if callback.id == -1:
            bot.send_message(callback.message.chat.id, mes, reply_markup=markup)
        else:
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda x: any(autobuy_list.filter(data=chk).check(x) for chk in ['spells_ab_add', 'spells_ab_del']))
    @logger.catch()
    def edit_spells_callback(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = autobuy_list.parse(callback.data)

        if data['data'] == 'spells_ab_add':
            bot.edit_message_text('Пришлите название спелла на РУССКОМ для добавление (0 для отмены):', callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, edit_spells_message, 'name_ru_spells', callback)
        elif data['data'] == 'spells_ab_del':
            bot.edit_message_text('Пришлите название спелла на русском или на английском для удаление (0 для отмены):',callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, edit_spells_message, 'del_spells', callback)

    @logger.catch()
    def edit_spells_message(message: Message, typ, callback: CallbackQuery, name_ru='', name_en=''):
        raw_text = message.text
        if raw_text == '0':
            if name_ru:
                if name_en:
                    config['autobuy_spells']['en'].pop(name_en)
                    config['autobuy_spells']['ru'].pop(name_ru)
            callback.id = -1
            edit_spells_callback_menu(callback)
        elif typ == 'del_spells':
            if raw_text in config['autobuy_spells']['ru']:
                config['autobuy_spells']['en'].pop(config['autobuy_spells']['ru'][raw_text]['en'])
                config['autobuy_spells']['ru'].pop(raw_text)
                callback.id = -1
                edit_spells_callback_menu(callback)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
            elif raw_text in config['autobuy_spells']['en']:
                config['autobuy_spells']['ru'].pop(config['autobuy_spells']['en'][raw_text]['ru'])
                config['autobuy_spells']['en'].pop(raw_text)
                callback.id = -1
                edit_spells_callback_menu(callback)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
            else:
                markup = InlineKeyboardMarkup()
                markup.add(create_button('Повторить', autobuy_list.new(data='spells_ab_del')))
                markup.add(create_button('Вернуться в меню', autobuy_list.new(data='edit_spells')))
                bot.send_message(message.chat.id, f'"{raw_text}" нету в спеллах!', reply_markup=markup)
        elif typ == 'name_ru_spells':
            bot.send_message(message.chat.id, 'Пришлите название счетчика на АНГЛИЙСКОМ для добавление (0 для отмены):')
            bot.register_next_step_handler(callback.message, edit_spells_message, 'name_en_spells', callback, name_ru=raw_text)
        elif typ == 'name_en_spells':
            config['autobuy_spells']['en'][raw_text] = {'ru': name_ru}
            config['autobuy_spells']['ru'][name_ru] = {'en': raw_text}
            bot.send_message(message.chat.id, 'Пришлите цену для покупки если нету в базе (0 для отмены):')
            bot.register_next_step_handler(callback.message, edit_spells_message, 'price_spells', callback, name_ru=name_ru, name_en=raw_text)
        elif typ == 'price_spells':
            try:
                config['autobuy_spells']['ru'][name_ru]['price'] = float(raw_text)
                config['autobuy_spells']['en'][name_en]['price'] = float(raw_text)
                bot.send_message(message.chat.id, 'Пришлите переплату из базы (0 для отмены):')
                bot.register_next_step_handler(callback.message, edit_spells_message, 'over_spells', callback, name_ru=name_ru, name_en=name_en)
            except:
                bot.send_message(message.chat.id, 'Неправильный формат!')
                bot.send_message(message.chat.id, 'Пришлите цену для покупки если нету в базе (0 для отмены):')
                bot.register_next_step_handler(callback.message, edit_spells_message, 'price_spells', callback, name_ru=name_ru, name_en=name_en)
        elif typ == 'over_spells':
            try:
                config['autobuy_spells']['ru'][name_ru]['over_price'] = float(raw_text)
                config['autobuy_spells']['en'][name_en]['over_price'] = float(raw_text)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
                callback.id = -1
                edit_spells_callback_menu(callback)
            except:
                bot.send_message(message.chat.id, 'Неправильный формат!')
                bot.send_message(message.chat.id, 'Пришлите переплату из базы (0 для отмены):')
                bot.register_next_step_handler(callback.message, edit_spells_message, 'over_spells', callback, name_ru=name_ru, name_en=name_en)

    @bot.callback_query_handler(func=lambda x: autobuy_list.filter(data='edit_unusual').check(x) or autobuy_list.filter(data='autobuy_unusual').check(x))
    @logger.catch()
    def edit_unusual_callback_menu(callback: CallbackQuery):
        if callback.id != -1:
            bot.answer_callback_query(callback.id)
            data = autobuy_list.parse(callback.data)
            if data['data'] != 'edit_unusual':
                setattr(tm, data['data'], not getattr(tm, data['data']))

        help1 = '\n'
        mes = (f'Настройка автопокупки для Unusual:\n\n'
               f'Unusual - {str(tm.autobuy_unusual).replace("False", "Отключено").replace("True", "Включено")}\n\n'
               f'Название - Цена покупки\n\n'
               f'{"".join(name + "/" + config["autobuy_unusual"]["ru"][name]["en"] + f" - " + str(config["autobuy_unusual"]["ru"][name]["price"]) + f"₽" + help1 for name in config["autobuy_unusual"]["ru"])[:-1]}')
        markup = InlineKeyboardMarkup()
        markup.add(create_button('Добавить', autobuy_list.new(data='unusual_ab_add')),
                   create_button('Удалить', autobuy_list.new(data='unusual_ab_del')))
        markup.add(create_button(f'{str(tm.autobuy_unusual).replace("False", "Включить").replace("True", "Выключить")}', autobuy_list.new(data='autobuy_unusual')))
        markup.add(create_button('Вернуться в меню', autobuy_list.new(data='menu')))
        if callback.id == -1:
            bot.send_message(callback.message.chat.id, mes, reply_markup=markup)
        else:
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda x: any(autobuy_list.filter(data=chk).check(x) for chk in ['unusual_ab_add', 'unusual_ab_del']))
    @logger.catch()
    def edit_unusual_callback(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = autobuy_list.parse(callback.data)

        if data['data'] == 'unusual_ab_add':
            bot.edit_message_text('Пришлите название эффекта на РУССКОМ для добавление (0 для отмены):', callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, edit_unusual_message, 'name_ru_unusual', callback)
        elif data['data'] == 'unusual_ab_del':
            bot.edit_message_text('Пришлите название эффекта на русском или на английском для удаление (0 для отмены):', callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, edit_unusual_message, 'del_unusual', callback)

    @logger.catch()
    def edit_unusual_message(message: Message, typ, callback: CallbackQuery, name_ru='', name_en=''):
        raw_text = message.text
        if raw_text == '0':
            if name_ru:
                if name_en:
                    config['autobuy_unusual']['en'].pop(name_en)
                    config['autobuy_unusual']['ru'].pop(name_ru)
            callback.id = -1
            edit_unusual_callback_menu(callback)
        elif typ == 'del_unusual':
            if raw_text in config['autobuy_unusual']['ru']:
                config['autobuy_unusual']['en'].pop(config['autobuy_unusual']['ru'][raw_text]['en'])
                config['autobuy_unusual']['ru'].pop(raw_text)
                callback.id = -1
                edit_unusual_callback_menu(callback)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
            elif raw_text in config['autobuy_unusual']['en']:
                config['autobuy_unusual']['ru'].pop(config['autobuy_unusual']['en'][raw_text]['ru'])
                config['autobuy_unusual']['en'].pop(raw_text)
                callback.id = -1
                edit_unusual_callback_menu(callback)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
            else:
                markup = InlineKeyboardMarkup()
                markup.add(create_button('Повторить', autobuy_list.new(data='unusual_ab_del')))
                markup.add(create_button('Вернуться в меню', autobuy_list.new(data='edit_unusual')))
                bot.send_message(message.chat.id, f'"{raw_text}" нету в эффектах!', reply_markup=markup)
        elif typ == 'name_ru_unusual':
            bot.send_message(message.chat.id, 'Пришлите название эффекта на АНГЛИЙСКОМ для добавление (0 для отмены):')
            bot.register_next_step_handler(callback.message, edit_unusual_message, 'name_en_unusual', callback, name_ru=raw_text)
        elif typ == 'name_en_unusual':
            config['autobuy_unusual']['en'][raw_text] = {'ru': name_ru}
            config['autobuy_unusual']['ru'][name_ru] = {'en': raw_text}
            bot.send_message(message.chat.id, 'Пришлите цену для покупки (0 для отмены):')
            bot.register_next_step_handler(callback.message, edit_unusual_message, 'price_unusual', callback, name_ru=name_ru, name_en=raw_text)
        elif typ == 'price_unusual':
            try:
                config['autobuy_unusual']['ru'][name_ru]['price'] = float(raw_text)
                config['autobuy_unusual']['en'][name_en]['price'] = float(raw_text)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
                callback.id = -1
                edit_unusual_callback_menu(callback)
            except:
                bot.send_message(message.chat.id, 'Неправильный формат!')
                bot.send_message(message.chat.id, 'Пришлите цену для покупки (0 для отмены):')
                bot.register_next_step_handler(callback.message, edit_unusual_message, 'price_unusual', callback, name_ru=name_ru, name_en=name_en)

    @bot.callback_query_handler(func=lambda x: autobuy_list.filter(data='edit_color').check(x) or autobuy_list.filter(data='autobuy_color').check(x))
    @logger.catch()
    def edit_color_callback_menu(callback: CallbackQuery):
        if callback.id != -1:
            bot.answer_callback_query(callback.id)
            data = autobuy_list.parse(callback.data)
            if data['data'] != 'edit_color':
                setattr(tm, data['data'], not getattr(tm, data['data']))

        help1 = '\n'
        mes = (f'Настройка автопокупки для Paint color:\n\n'
               f'Paint Color  - {str(tm.autobuy_color).replace("False", "Отключено").replace("True", "Включено")}\n\n'
               f'Название - Цена покупки\n\n'
               f'{"".join(name + "/" + config["autobuy_color"]["ru"][name]["en"] + f" - " + str(config["autobuy_color"]["ru"][name]["price"]) + f"₽" + help1 for name in config["autobuy_color"]["ru"])[:-1]}')
        markup = InlineKeyboardMarkup()
        markup.add(create_button('Добавить', autobuy_list.new(data='color_ab_add')),
                   create_button('Удалить', autobuy_list.new(data='color_ab_del')))
        markup.add(create_button(f'{str(tm.autobuy_color).replace("False", "Включить").replace("True", "Выключить")}', autobuy_list.new(data='autobuy_color')))
        markup.add(create_button('Вернуться в меню', autobuy_list.new(data='menu')))
        if callback.id == -1:
            bot.send_message(callback.message.chat.id, mes, reply_markup=markup)
        else:
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda x: any(autobuy_list.filter(data=chk).check(x) for chk in ['color_ab_add', 'color_ab_del']))
    @logger.catch()
    def edit_color_callback(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = autobuy_list.parse(callback.data)

        if data['data'] == 'color_ab_add':
            bot.edit_message_text('Пришлите название краски на РУССКОМ для добавление (0 для отмены):', callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, edit_color_message, 'name_ru_color', callback)
        elif data['data'] == 'color_ab_del':
            bot.edit_message_text('Пришлите название краски на русском или на английском для удаление (0 для отмены):', callback.message.chat.id,callback.message.message_id)
            bot.register_next_step_handler(callback.message, edit_color_message, 'del_color', callback)

    @logger.catch()
    def edit_color_message(message: Message, typ, callback: CallbackQuery, name_ru='', name_en=''):
        raw_text = message.text
        if raw_text == '0':
            if name_ru:
                if name_en:
                    config['autobuy_color']['en'].pop(name_en)
                    config['autobuy_color']['ru'].pop(name_ru)
            callback.id = -1
            edit_color_callback_menu(callback)
        elif typ == 'del_color':
            if raw_text in config['autobuy_color']['ru']:
                config['autobuy_color']['en'].pop(config['autobuy_color']['ru'][raw_text]['en'])
                config['autobuy_color']['ru'].pop(raw_text)
                callback.id = -1
                edit_color_callback_menu(callback)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
            elif raw_text in config['autobuy_color']['en']:
                config['autobuy_color']['ru'].pop(config['autobuy_color']['en'][raw_text]['ru'])
                config['autobuy_color']['en'].pop(raw_text)
                callback.id = -1
                edit_color_callback_menu(callback)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
            else:
                markup = InlineKeyboardMarkup()
                markup.add(create_button('Повторить', autobuy_list.new(data='color_ab_del')))
                markup.add(create_button('Вернуться в меню', autobuy_list.new(data='edit_color')))
                bot.send_message(message.chat.id, f'"{raw_text}" нету в красках!', reply_markup=markup)
        elif typ == 'name_ru_color':
            bot.send_message(message.chat.id, 'Пришлите название краски на АНГЛИЙСКОМ для добавление (0 для отмены):')
            bot.register_next_step_handler(callback.message, edit_color_message, 'name_en_color', callback, name_ru=raw_text)
        elif typ == 'name_en_color':
            config['autobuy_color']['en'][raw_text] = {'ru': name_ru}
            config['autobuy_color']['ru'][name_ru] = {'en': raw_text}
            bot.send_message(message.chat.id, 'Пришлите цену для покупки (0 для отмены):')
            bot.register_next_step_handler(callback.message, edit_color_message, 'price_color', callback, name_ru=name_ru, name_en=raw_text)
        elif typ == 'price_color':
            try:
                config['autobuy_color']['ru'][name_ru]['price'] = float(raw_text)
                config['autobuy_color']['en'][name_en]['price'] = float(raw_text)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
                callback.id = -1
                edit_color_callback_menu(callback)
            except:
                bot.send_message(message.chat.id, 'Неправильный формат!')
                bot.send_message(message.chat.id, 'Пришлите цену для покупки (0 для отмены):')
                bot.register_next_step_handler(callback.message, edit_color_message, 'price_color', callback, name_ru=name_ru, name_en=name_en)

    @bot.callback_query_handler(func=lambda x: autobuy_list.filter(data='edit_scores').check(x) or autobuy_list.filter(data='autobuy_scores').check(x))
    @logger.catch()
    def edit_scores_callback_menu(callback: CallbackQuery):
        if callback.id != -1:
            bot.answer_callback_query(callback.id)
            data = autobuy_list.parse(callback.data)
            if data['data'] != 'edit_scores':
                setattr(tm, data['data'], not getattr(tm, data['data']))
        help1 = '\n'
        mes = (f'Настройка автопокупки для счетчиков:\n\n'
               f'Scores - {str(tm.autobuy_scores).replace("False", "Отключено").replace("True", "Включено")}\n\n'
               f'Название - Макс.цена - Переплата\n\n'
               f'{"".join(name + "/" + config["autobuy_scores"]["ru"][name]["en"] + f" - " + str(config["autobuy_scores"]["ru"][name]["max_price"]) + f"₽ - " + str(config["autobuy_scores"]["ru"][name]["over_price"]) + "₽" + help1 for name in config["autobuy_scores"]["ru"])[:-1]}')
        markup = InlineKeyboardMarkup()
        markup.add(create_button('Добавить', autobuy_list.new(data='scores_ab_add')),
                   create_button('Удалить', autobuy_list.new(data='scores_ab_del')))
        markup.add(create_button(f'{str(tm.autobuy_scores).replace("False", "Включить").replace("True", "Выключить")}', autobuy_list.new(data='autobuy_scores')))
        markup.add(create_button('Вернуться в меню', autobuy_list.new(data='menu')))
        if callback.id == -1:
            bot.send_message(callback.message.chat.id, mes, reply_markup=markup)
        else:
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda x: any(autobuy_list.filter(data=chk).check(x) for chk in ['scores_ab_add', 'scores_ab_del']))
    @logger.catch()
    def edit_scores_callback(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = autobuy_list.parse(callback.data)

        if data['data'] == 'scores_ab_add':
            bot.edit_message_text('Пришлите название счетчика на РУССКОМ для добавление (0 для отмены):', callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, edit_scores_message ,'name_ru_score', callback)
        elif data['data'] == 'scores_ab_del':
            bot.edit_message_text('Пришлите название счетчика на русском или на английском для удаление (0 для отмены):', callback.message.chat.id,callback.message.message_id)
            bot.register_next_step_handler(callback.message, edit_scores_message, 'del_score', callback)

    @logger.catch()
    def edit_scores_message(message: Message, typ, callback: CallbackQuery, name_ru='', name_en=''):
        raw_text = message.text
        if raw_text == '0':
            if name_ru:
                if name_en:
                    config['autobuy_scores']['en'].pop(name_en)
                    config['autobuy_scores']['ru'].pop(name_ru)
            callback.id = -1
            edit_scores_callback_menu(callback)
        elif typ == 'del_score':
            if raw_text in config['autobuy_scores']['ru']:
                config['autobuy_scores']['en'].pop(config['autobuy_scores']['ru'][raw_text]['en'])
                config['autobuy_scores']['ru'].pop(raw_text)
                callback.id = -1
                edit_scores_callback_menu(callback)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
            elif raw_text in config['autobuy_scores']['en']:
                config['autobuy_scores']['ru'].pop(config['autobuy_scores']['en'][raw_text]['ru'])
                config['autobuy_scores']['en'].pop(raw_text)
                callback.id = -1
                edit_scores_callback_menu(callback)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
            else:
                markup = InlineKeyboardMarkup()
                markup.add(create_button('Повторить', autobuy_list.new(data='scores_ab_del')))
                markup.add(create_button('Вернуться в меню', autobuy_list.new(data='edit_scores')))
                bot.send_message(message.chat.id, f'"{raw_text}" нету в счетчиках!', reply_markup=markup)
        elif typ == 'name_ru_score':
            bot.send_message(message.chat.id, 'Пришлите название счетчика на АНГЛИЙСКОМ для добавление (0 для отмены):')
            bot.register_next_step_handler(callback.message, edit_scores_message, 'name_en_score', callback, name_ru=raw_text)
        elif typ == 'name_en_score':
            config['autobuy_scores']['en'][raw_text] = {'ru': name_ru}
            config['autobuy_scores']['ru'][name_ru] = {'en': raw_text}
            bot.send_message(message.chat.id, 'Пришлите максимальную цену (0 для отмены):')
            bot.register_next_step_handler(callback.message, edit_scores_message, 'max_score', callback, name_ru=name_ru, name_en=raw_text)
        elif typ == 'max_score':
            try:
                config['autobuy_scores']['ru'][name_ru]['max_price'] = float(raw_text)
                config['autobuy_scores']['en'][name_en]['max_price'] = float(raw_text)
                bot.send_message(message.chat.id, 'Пришлите переплату из базы (0 для отмены):')
                bot.register_next_step_handler(callback.message, edit_scores_message, 'over_score', callback,  name_ru=name_ru, name_en=name_en)
            except:
                bot.send_message(message.chat.id, 'Неправильный формат!')
                bot.send_message(message.chat.id, 'Пришлите максимальную цену (0 для отмены):')
                bot.register_next_step_handler(callback.message, edit_scores_message, 'max_score', callback,  name_ru=name_ru, name_en=name_en)
        elif typ == 'over_score':
            try:
                config['autobuy_scores']['ru'][name_ru]['over_price'] = float(raw_text)
                config['autobuy_scores']['en'][name_en]['over_price'] = float(raw_text)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
                callback.id = -1
                edit_scores_callback_menu(callback)
            except:
                bot.send_message(message.chat.id, 'Неправильный формат!')
                bot.send_message(message.chat.id, 'Пришлите переплату из базы (0 для отмены):')
                bot.register_next_step_handler(callback.message, edit_scores_message, 'over_score', callback,  name_ru=name_ru, name_en=name_en)

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

    @logger.catch()
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

    @bot.callback_query_handler(func=lambda x: notification_list.filter(data='menu').check(x))
    @logger.catch()
    def notification_menu(callback: CallbackQuery):
        if callback.id != -1:
            bot.answer_callback_query(callback.id)

        help1 = '\n'
        mes = (f'Настройка уведомлений:\n\n'
               f'Paint Color:\n'
               f'{"".join(name + "/" + config["notification_color"]["ru"][name]["en"] + f" - До " + str(config["notification_color"]["ru"][name]["price"]) + f"₽" + help1 for name in config["notification_color"]["ru"])}\n'
               f'Счётчики:\n'
               f'{"".join(name + "/" + config["notification_score"]["ru"][name]["en"] + f" - До " + str(config["notification_score"]["ru"][name]["price"]) + f"₽" + help1 for name in config["notification_score"]["ru"])[:-1]}')
        markup = InlineKeyboardMarkup()
        markup.add(create_button('Настройка Paint Color', notification_list.new(data='edit_color')))
        markup.add(create_button('Настройка счётчиков', notification_list.new(data='edit_score')))
        markup.add(create_button('Вернуться в меню', menu_page.new(page='menu')))
        if callback.id != -1:
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)
        else:
            bot.send_message(callback.message.chat.id, mes, reply_markup=markup)

    @bot.callback_query_handler(func=lambda x: any(notification_list.filter(data=chk).check(x) for chk in ['edit_color', 'color_add', 'color_del']))
    @logger.catch()
    def notification_edit_color_callback(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = notification_list.parse(callback.data)
        if data['data'] == 'edit_color':
            mes = 'Выберите:'
            markup = InlineKeyboardMarkup()
            markup.add(create_button('Добавить', notification_list.new(data='color_add')), create_button('Удалить', notification_list.new(data='color_del')))
            markup.add(create_button('Вернуться в меню', notification_list.new(data='menu')))
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)
        elif data['data'] == 'color_add':
            mes = 'Пришлите название краски на РУССКОМ (0 для отмены):'
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, notification_edit_color_message, 'name_ru_color', callback)
        elif data['data'] == 'color_del':
            mes = 'Пришлите название краски на русском или на английском для удаление (0 для отмены):'
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, notification_edit_color_message, 'del_color', callback)

    @logger.catch()
    def notification_edit_color_message(message: Message, typ, callback: CallbackQuery, name_ru='', name_en=''):
        raw_text = message.text
        if raw_text == '0':
            if name_ru:
                if name_en:
                    config['notification_color']['en'].pop(name_en)
                    config['notification_color']['ru'].pop(name_ru)
            callback.id = -1
            notification_menu(callback)
        elif typ == 'del_color':
            if raw_text in config['notification_color']['ru']:
                config['notification_color']['en'].pop(config['notification_color']['ru'][raw_text]['en'])
                config['notification_color']['ru'].pop(raw_text)
                callback.id = -1
                notification_menu(callback)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
            elif raw_text in config['notification_color']['en']:
                config['notification_color']['ru'].pop(config['notification_color']['en'][raw_text]['ru'])
                config['notification_color']['en'].pop(raw_text)
                callback.id = -1
                notification_menu(callback)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
            else:
                markup = InlineKeyboardMarkup()
                markup.add(create_button('Повторить', autobuy_list.new(data='color_ab_del')))
                markup.add(create_button('Вернуться в меню', autobuy_list.new(data='edit_color')))
                bot.send_message(message.chat.id, f'"{raw_text}" нету в красках!', reply_markup=markup)
        elif typ == 'name_ru_color':
            bot.send_message(message.chat.id, 'Пришлите название краски на АНГЛИЙСКОМ для добавление (0 для отмены):')
            bot.register_next_step_handler(callback.message, notification_edit_color_message, 'name_en_color', callback, name_ru=raw_text)
        elif typ == 'name_en_color':
            config['notification_color']['en'][raw_text] = {'ru': name_ru}
            config['notification_color']['ru'][name_ru] = {'en': raw_text}
            bot.send_message(message.chat.id, 'Пришлите цену для уведомлении (0 для отмены):')
            bot.register_next_step_handler(callback.message, notification_edit_color_message, 'price_color', callback, name_ru=name_ru, name_en=raw_text)
        elif typ == 'price_color':
            try:
                config['notification_color']['ru'][name_ru]['price'] = float(raw_text)
                config['notification_color']['en'][name_en]['price'] = float(raw_text)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
                callback.id = -1
                notification_menu(callback)
            except:
                bot.send_message(message.chat.id, 'Неправильный формат!')
                bot.send_message(message.chat.id, 'Пришлите цену для уведомлении (0 для отмены):')
                bot.register_next_step_handler(callback.message, notification_edit_color_message, 'price_color', callback, name_ru=name_ru, name_en=name_en)

    @bot.callback_query_handler(func=lambda x: any(
        notification_list.filter(data=chk).check(x) for chk in ['edit_score', 'score_add', 'score_del']))
    @logger.catch()
    def notification_edit_color_callback(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = notification_list.parse(callback.data)
        if data['data'] == 'edit_score':
            mes = 'Выберите:'
            markup = InlineKeyboardMarkup()
            markup.add(create_button('Добавить', notification_list.new(data='score_add')),
                       create_button('Удалить', notification_list.new(data='score_del')))
            markup.add(create_button('Вернуться в меню', notification_list.new(data='menu')))
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)
        elif data['data'] == 'score_add':
            mes = 'Пришлите название счетчика на РУССКОМ (0 для отмены):'
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, notification_edit_score_message, 'name_ru_color', callback)
        elif data['data'] == 'score_del':
            mes = 'Пришлите название счетчика на русском или на английском для удаление (0 для отмены):'
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, notification_edit_score_message, 'del_color', callback)

    @logger.catch()
    def notification_edit_score_message(message: Message, typ, callback: CallbackQuery, name_ru='', name_en=''):
        raw_text = message.text
        if raw_text == '0':
            if name_ru:
                if name_en:
                    config['notification_score']['en'].pop(name_en)
                    config['notification_score']['ru'].pop(name_ru)
            callback.id = -1
            notification_menu(callback)
        elif typ == 'del_color':
            if raw_text in config['notification_score']['ru']:
                config['notification_score']['en'].pop(config['notification_score']['ru'][raw_text]['en'])
                config['notification_score']['ru'].pop(raw_text)
                callback.id = -1
                notification_menu(callback)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
            elif raw_text in config['notification_score']['en']:
                config['notification_score']['ru'].pop(config['notification_score']['en'][raw_text]['ru'])
                config['notification_score']['en'].pop(raw_text)
                callback.id = -1
                notification_menu(callback)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
            else:
                markup = InlineKeyboardMarkup()
                markup.add(create_button('Повторить', autobuy_list.new(data='color_ab_del')))
                markup.add(create_button('Вернуться в меню', autobuy_list.new(data='edit_color')))
                bot.send_message(message.chat.id, f'"{raw_text}" нету в красках!', reply_markup=markup)
        elif typ == 'name_ru_color':
            bot.send_message(message.chat.id, 'Пришлите название счетчика на АНГЛИЙСКОМ для добавление (0 для отмены):')
            bot.register_next_step_handler(callback.message, notification_edit_score_message, 'name_en_color', callback,
                                           name_ru=raw_text)
        elif typ == 'name_en_color':
            config['notification_score']['en'][raw_text] = {'ru': name_ru}
            config['notification_score']['ru'][name_ru] = {'en': raw_text}
            bot.send_message(message.chat.id, 'Пришлите цену для уведомлении (0 для отмены):')
            bot.register_next_step_handler(callback.message, notification_edit_score_message, 'price_color', callback,
                                           name_ru=name_ru, name_en=raw_text)
        elif typ == 'price_color':
            try:
                config['notification_score']['ru'][name_ru]['price'] = float(raw_text)
                config['notification_score']['en'][name_en]['price'] = float(raw_text)
                with open('./data/config.json', 'w', encoding='utf-8') as file:
                    json.dump(config, file, ensure_ascii=False, indent=4)
                callback.id = -1
                notification_menu(callback)
            except:
                bot.send_message(message.chat.id, 'Неправильный формат!')
                bot.send_message(message.chat.id, 'Пришлите цену для уведомлении (0 для отмены):')
                bot.register_next_step_handler(callback.message, notification_edit_score_message, 'price_color',
                                               callback, name_ru=name_ru, name_en=name_en)


    @bot.callback_query_handler(func= lambda x: x.data == 'huyhuy')
    def void_answer_callback(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)

    @bot.callback_query_handler(func=lambda x: autobuy_list.filter().check(x))
    @logger.catch()
    def huyhuyv2(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        print(callback.data)
