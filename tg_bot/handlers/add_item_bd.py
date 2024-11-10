from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, CallbackQuery
from utils.loging import logger
from utils.loading_data import items_bd, items_bd_list, items_bd_list_unusual, items_unusual_bd, items_cache
from utils.config import config
from tg_bot.callbacks_data import menu_page, add_item_select
import json
from tg_bot.utils import create_button, cancel


add_item = [0]

def run(bot: TeleBot, tm):
    # Запуск добавление предмета
    @bot.callback_query_handler(func=lambda x: menu_page.filter(page='add_item').check(x))
    @logger.catch()
    def menu_base_add_item(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        mes = ('Пришлите название предмета (0 для отмены):')
        bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id)
        bot.register_next_step_handler(callback.message, base_add_item_select, 'name')

    # Проверка название предмета и регистрация сообщения
    @logger.catch()
    def base_add_item_select(message: Message, type: str):
        if type == 'name':
            flag = True
            if add_item[0] != 0:
                item_name = add_item[0]
                flag = False
            else:
                item_name = message.text
            if item_name == '0':
                cancel(bot, message.chat.id)
                return 0
            if 'Unusual' == item_name:
                bot.send_message(message.chat.id, 'Предмет Unusual невозможно добавить!')
                add_item[0] = 0
                return 0

            if (item_name in items_bd or item_name in items_unusual_bd) and flag:
                mes = (f'Предмет {item_name} уже есть в базе данных.\n'
                       f'Вы уверены, что хотите его перезаписать?')
                markup = InlineKeyboardMarkup()
                markup.add(*[create_button('Да', add_item_select.new(select='yes', type='sure')),
                             create_button('Нет', add_item_select.new(select='no', type='sure'))])
                add_item[0] = item_name
                bot.send_message(message.chat.id, mes, reply_markup=markup)
                return 0

            add_item[0] = {'name': item_name, item_name: {}}
            add_item[0]['cancel_full'] = True
            add_item[0]['status'] = 'name'
            add_item[0]['unusual_flag'] = False
            add_item[0]['cancel_status'] = ''
            mes = 'Выберите тип предмета:'
            markup = InlineKeyboardMarkup()
            unusual = ''
            if 'Unusual' == item_name[:7]:
                add_item[0]['unusual_flag'] = True
                unusual = 'unusual-'

            markup.add(*[create_button('Craftable', add_item_select.new(select='Craftable', type=f'{unusual}craft')),
                         create_button('Non-Craftable',
                                       add_item_select.new(select='Non-Craftable', type=f'{unusual}craft'))])
            markup.add(create_button('Отмена', add_item_select.new(select='name', type='cancel')))
            if flag:
                bot.send_message(message.chat.id, mes, reply_markup=markup)
            else:
                bot.edit_message_text(mes, message.chat.id, message.message_id, reply_markup=markup)
        if type == 'craft':
            add_item[0]['status'] = 'craft'
            mes = 'Выберите валюту:'
            markup = InlineKeyboardMarkup()
            markup.add(*[create_button('Metal', add_item_select.new(select='metal', type='currency')),
                         create_button('Keys', add_item_select.new(select='keys', type='currency'))])
            markup.add(create_button('Отмена', add_item_select.new(select='craft', type='cancel')))
            if add_item[0]['unusual_flag']:
                if message.text == '0':
                    add_item[0]['cancel_status'] = 'unusual-craft'
                    if add_item[0]['cancel_full']:
                        cancel(bot, message.chat.id)
                        return 0
                    elif len(list(add_item[0][add_item[0]['name']][add_item[0]['last-craft']]['Particles'])) == 0:
                        add_item[0][add_item[0]['name']].pop(add_item[0]['last-craft'])
                        add_item[0]['last-craft'] = list(add_item[0][add_item[0]['name']].keys())[0]
                        base_add_item_select(message, 'price')
                        return 0
                    else:
                        base_add_item_select(message, 'price')
                        return 0
                particle = message.text
                add_item[0][add_item[0]['name']][add_item[0]['last-craft']]['Particles'][particle] = {}
                add_item[0]['last-particle'] = particle

                bot.send_message(message.chat.id, mes, reply_markup=markup)
            else:
                bot.edit_message_text(mes, message.chat.id, message.message_id, reply_markup=markup)
        if type == 'currency':
            add_item[0]['status'] = 'currency'
            mes = 'Пришлите цену предмета (0 для отмены):'
            bot.edit_message_text(mes, message.chat.id, message.message_id)
            bot.register_next_step_handler(message, base_add_item_select, 'price')
        if type == 'price':
            markup = InlineKeyboardMarkup()
            unusual = ''
            if add_item[0]['status'] == 'currency':
                if add_item[0]['cancel_status'] == '':
                    if message.text == '0' and add_item[0]['cancel_full']:
                        cancel(bot, message.chat.id)
                        return 0
                    elif message.text == '0':
                        if add_item[0]['unusual_flag']:
                            add_item[0]['cancel_status'] = 'price'
                            if len(list(add_item[0][add_item[0]['name']][add_item[0]['last-craft']]['Particles'])) <= 1:
                                add_item[0][add_item[0]['name']].pop(add_item[0]['last-craft'])
                                add_item[0]['last-craft'] = list(add_item[0][add_item[0]['name']].keys())[0]
                            else:
                                add_item[0][add_item[0]['name']][add_item[0]['last-craft']]['Particles'].pop(
                                    add_item[0]['last-particle'])
                                add_item[0]['last-particle'] = ''
                        else:
                            add_item[0]['cancel_status'] = 'price'
                            add_item[0][add_item[0]['name']].pop(add_item[0]['last-craft'])
                            add_item[0]['last-craft'] = list(add_item[0][add_item[0]['name']].keys())[0]
                    else:
                        try:
                            price = float(message.text)
                        except:
                            bot.send_message(message.chat.id, 'Неверный формат!')
                            mes = bot.send_message(message.chat.id, 'пум...')
                            base_add_item_select(mes, 'currency')
                            return 0
                        if add_item[0]['unusual_flag']:
                            add_item[0][add_item[0]['name']][add_item[0]['last-craft']]['Particles'][
                                add_item[0]['last-particle']]['price'] = price
                        else:
                            add_item[0][add_item[0]['name']][add_item[0]['last-craft']]['price'] = price
            add_item[0]['status'] = 'price'
            if add_item[0]['cancel_full']:
                add_item[0]['cancel_full'] = False
            if add_item[0]['unusual_flag']:
                markup.add(create_button('Добавить еще эффект', add_item_select.new(select='0', type='add_effect')))
                unusual = 'unusual-'
                add_item[0]['last-particle'] = ''
            if 'Non-Craftable' not in add_item[0][add_item[0]['name']]:
                markup.add(create_button('Добавить Non-Craftable',
                                         add_item_select.new(select='Non-Craftable', type=f'{unusual}craft')))
            elif 'Craftable' not in add_item[0][add_item[0]['name']]:
                markup.add(create_button('Добавить Craftable',
                                         add_item_select.new(select='Craftable', type=f'{unusual}craft')))
            markup.add(*[create_button('Отмена', add_item_select.new(select='last', type='cancel')),
                         create_button('Готово', add_item_select.new(select='', type='ready'))])

            mes = f'Предмет: {add_item[0]["name"]}\n\n'
            if 'Unusual' == add_item[0]['name'][:7]:
                for craft in add_item[0][add_item[0]['name']]:
                    mes += f'{craft}:\n'
                    mes += f'\t\tЭффекты:\n'
                    for particl in add_item[0][add_item[0]['name']][craft]['Particles']:
                        mes += (f'\t\t\t\tЭффект: {particl}\n'
                                f'\t\t\t\tЦеник: {add_item[0][add_item[0]["name"]][craft]["Particles"][particl]["price"]} {add_item[0][add_item[0]["name"]][craft]["Particles"][particl]["currency"]}\n'
                                f'\t\t\t\tЦеник в рублях: {config["currency"][add_item[0][add_item[0]["name"]][craft]["Particles"][particl]["currency"]] * add_item[0][add_item[0]["name"]][craft]["Particles"][particl]["price"]} ₽\n\n')
            else:
                for craft in add_item[0][add_item[0]['name']]:
                    mes += (f'{craft}:\n'
                            f'\t\tЦеник: {add_item[0][add_item[0]["name"]][craft]["price"]} {add_item[0][add_item[0]["name"]][craft]["currency"]}\n'
                            f'\t\tЦеник в рублях: {config["currency"][add_item[0][add_item[0]["name"]][craft]["currency"]] * add_item[0][add_item[0]["name"]][craft]["price"]} ₽\n\n')

            if not any([add_item[0]['cancel_status'] == '', add_item[0]['cancel_status'] == 'price',
                        add_item[0]['cancel_status'] == 'unusual-craft']):
                bot.edit_message_text(mes, message.chat.id, message.message_id, reply_markup=markup)
                add_item[0]['cancel_status'] = ''
                return 0
            bot.send_message(message.chat.id, mes, reply_markup=markup)
            add_item[0]['cancel_status'] = ''
        if type == 'unusual-craft':
            if 'Particles' not in add_item[0][add_item[0]['name']][add_item[0]['last-craft']]:
                add_item[0][add_item[0]['name']][add_item[0]['last-craft']]['Particles'] = {}
            mes = "Пришлите название эффекта (0 для отмены):"
            add_item[0]['status'] = 'craft'
            bot.edit_message_text(mes, message.chat.id, message.message_id)
            bot.register_next_step_handler(message, base_add_item_select, 'craft')

    # Каллбак обработчик для добавление сообщение
    @bot.callback_query_handler(func=lambda x: add_item_select.filter().check(x))
    @logger.catch()
    def base_add_item_select_callback(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = add_item_select.parse(callback.data)
        if data['type'] == 'cancel':
            if add_item[0]['cancel_full'] == True or data['select'] == 'last':
                cancel(bot, callback.message.chat.id, callback.message)
                return 0
            else:
                add_item[0]['cancel_status'] = data['select']
                if add_item[0]['unusual_flag']:
                    if len(list(add_item[0][add_item[0]['name']][add_item[0]['last-craft']]['Particles'])) <= 1:
                        add_item[0][add_item[0]['name']].pop(add_item[0]['last-craft'])
                        add_item[0]['last-craft'] = list(add_item[0][add_item[0]['name']].keys())[0]
                        base_add_item_select(callback.message, 'price')
                        return 0
                    else:
                        add_item[0][add_item[0]['name']][add_item[0]['last-craft']]['Particles'].pop(
                            add_item[0]['last-particle'])
                        add_item[0]['last-particle'] = ''
                        base_add_item_select(callback.message, 'price')
                        return 0
                else:
                    add_item[0][add_item[0]['name']].pop(add_item[0]['last-craft'])
                    add_item[0]['last-craft'] = list(add_item[0][add_item[0]['name']].keys())[0]
                    base_add_item_select(callback.message, 'price')
                    return 0

        elif data['type'] == 'craft' or data['type'] == 'unusual-craft':
            add_item[0][add_item[0]['name']][data['select']] = {}
            add_item[0]['last-craft'] = data['select']
            if data['type'] == 'unusual-craft':
                add_item[0]['last-particle'] = ''

        elif data['type'] == 'currency':
            if 'last-particle' in add_item[0]:
                add_item[0][add_item[0]['name']][add_item[0]['last-craft']]['Particles'][add_item[0]['last-particle']][
                    'currency'] = data['select']
            else:
                add_item[0][add_item[0]['name']][add_item[0]['last-craft']]['currency'] = data['select']
        elif data['type'] == 'add_effect':
            data['type'] = 'unusual-craft'
        elif data['type'] == 'sure':
            if data['select'] == 'no':
                cancel(bot, callback.message.chat.id, callback.message)
                return 0
            if data['select'] == 'yes':
                base_add_item_select(callback.message, 'name')
                return 0
        elif data['type'] == 'ready':
            try:
                if 'Unusual' == add_item[0]['name'][:7]:
                    items_unusual_bd[add_item[0]['name']] = add_item[0][add_item[0]['name']]
                    items_bd_list_unusual.append(add_item[0]['name'])
                    with open('./items/unusual_items.json', 'w', encoding='UTF-8') as file:
                        json.dump(items_unusual_bd, file, indent=4, ensure_ascii=False)
                else:
                    items_bd[add_item[0]['name']] = add_item[0][add_item[0]['name']]
                    items_bd_list.append(add_item[0]['name'])
                    with open('./items/items.json', 'w', encoding='utf-8') as file:
                        json.dump(items_bd, file, indent=4, ensure_ascii=False)
                bot.edit_message_text(callback.message.text, callback.message.chat.id, callback.message.message_id)
                bot.send_message(callback.message.chat.id, 'Успешно добавлено!')
            except Exception as ex:
                bot.edit_message_text(callback.message.text, callback.message.chat.id, callback.message.message_id)
                bot.send_message(callback.message.chat.id,
                                 'Ошибка при сохранение в базе данных, обратитесь администратору!')
                logger.exception(f'Fail save items bd. Exceptions: {ex}')
            add_item[0] = 0

        base_add_item_select(callback.message, data['type'])