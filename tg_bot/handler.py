import telebot.types
from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from utils.loging import logger
from utils.loading_data import items_bd, items_bd_list, items_bd_list_unusual, items_unusual_bd
from utils.config import config
from tg_bot.callbacks_data import menu_page, list_menu, base_item, add_item_select, item_message
import json
from parsing import TM_Parsing


def create_button(text: str, callback: str):
    return InlineKeyboardButton(text=text, callback_data=callback)

def cancel(bot: TeleBot,chat_id, message: Message=None):
    if message:
        bot.edit_message_text('Отмена действий!', chat_id, message.message_id)
    else:
        bot.send_message(chat_id, 'Отмена действий!')
    add_item[0] = 0


def get_search_items(text):
    result = []
    if 'unusual' == text[:7]:
        text = text[7:]
        for item in items_unusual_bd:
            if text in item.lower():
                result.append(item)
    else:
        for item in items_bd:
            if text in item.lower():
                result.append(item)
    return result

add_item = [0]

confirm_func = {}

def run(bot: TeleBot, tm: TM_Parsing):
    logger.debug('Starting handlers telegram bot')

    @bot.message_handler(commands=['test'])  #TODO: Command test
    @logger.catch()
    def command_test(message: Message):
        bot.send_message(message.chat.id, f'Chat id: {message.chat.id}\nThread id: {message.message_thread_id}',
                         message_thread_id=message.message_thread_id, reply_markup=telebot.types.ReplyKeyboardRemove())
        print(len(bot.message_handlers))

    @bot.message_handler(commands=['stop'])
    def command_stop(message: Message):
        tm.parsing_status_url = False

    @bot.message_handler(commands=['start'])
    def command_start(message: Message):
        tm.start_thread_parsing_url()


    @bot.message_handler(commands=['menu'])
    @logger.catch()
    def command_menu(message: Message):
        mes = (f'STATUS:\n'
               f'{tm.parsing_status_url}\n'
               f'{tm.parsing_status_websocket}')
        markup = InlineKeyboardMarkup()
        buttons = [create_button('Проверить предмет', menu_page.new('check_id')),
                   create_button('Открыть базу', menu_page.new('base')),
                   create_button('Удалить предмет', menu_page.new('delete_item')),
                   create_button('Меню автобая', menu_page.new('autobuy_menu')),
                   create_button('Очистить кэш', menu_page.new('clear_cache')),
                   create_button('Изменить курс', menu_page.new('change_currency'))]
        markup.add(buttons[3], buttons[1])
        markup.add(buttons[0], buttons[2])
        markup.add(buttons[4])
        bot.send_message(message.chat.id, mes, reply_markup=markup)

    @bot.callback_query_handler(func=lambda x: menu_page.filter(page='base').check(x))
    @logger.catch()
    def menu_base(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        count_not_unusual_items = len(items_bd)-1
        count_unusual_items = len(items_unusual_bd)
        count_all_items = count_unusual_items + count_not_unusual_items
        mes = (f"Кол-во предметов: {count_not_unusual_items} шт.\n"
               f"Кол-во unusual предметов: {count_unusual_items} шт.\n\n"
               f"Всего предметов: {count_all_items} шт.")
        markup = InlineKeyboardMarkup()
        buttons = [create_button('Добавить предмет', menu_page.new(page='add_item')),
                   create_button('Найти предмет', menu_page.new(page='find_item'))]
        markup.add(*buttons)
        bot.edit_message_text(text=mes, chat_id=callback.message.chat.id, message_id=callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func= lambda x: menu_page.filter(page='add_item').check(x))
    @logger.catch()
    def menu_base_add_item(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        mes = ('Пришлите название предмета (0 для отмены):')
        bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id)
        bot.register_next_step_handler(callback.message, base_add_item_select, 'name')

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

            add_item[0] = {'name': item_name, item_name:{}}
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
                        create_button('Non-Craftable', add_item_select.new(select='Non-Craftable', type=f'{unusual}craft'))])
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
                                add_item[0][add_item[0]['name']][add_item[0]['last-craft']]['Particles'].pop(add_item[0]['last-particle'])
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
                            add_item[0][add_item[0]['name']][add_item[0]['last-craft']]['Particles'][add_item[0]['last-particle']]['price'] = price
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
                markup.add(create_button('Добавить Non-Craftable', add_item_select.new(select='Non-Craftable', type=f'{unusual}craft')))
            elif 'Craftable' not in add_item[0][add_item[0]['name']]:
                markup.add(create_button('Добавить Craftable', add_item_select.new(select='Craftable', type=f'{unusual}craft')))
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

            if not any([add_item[0]['cancel_status'] == '', add_item[0]['cancel_status'] == 'price', add_item[0]['cancel_status'] == 'unusual-craft']):
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



    @bot.callback_query_handler(func= lambda x: add_item_select.filter().check(x))
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
                        add_item[0][add_item[0]['name']][add_item[0]['last-craft']]['Particles'].pop(add_item[0]['last-particle'])
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
                add_item[0][add_item[0]['name']][add_item[0]['last-craft']]['Particles'][add_item[0]['last-particle']]['currency'] = data['select']
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
                bot.send_message(callback.message.chat.id, 'Ошибка при сохранение в базе данных, обратитесь администратору!')
                logger.exception(f'Fail save items bd. Exceptions: {ex}')
            add_item[0] = 0

        base_add_item_select(callback.message, data['type'])



    @bot.callback_query_handler(func= lambda x: menu_page.filter(page='find_item').check(x))
    @logger.catch()
    def menu_base_find_item(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        bot.edit_message_text('Пришлите название предмета', callback.message.chat.id, callback.message.message_id)
        bot.register_next_step_handler_by_chat_id(callback.message.chat.id, menu_base_search_item)

    @logger.catch()
    def menu_base_search_item(message: Message, callback: CallbackQuery = None, page=0):
        if callback == None:
            text = message.text.lower()
        else:
            text = list_menu.parse(callback.data)['text']
        result = get_search_items(text)
        unusual_flag = ''
        if 'unusual' == text[:7]:
            unusual_flag = 'True'
        mes = f"Найдено {len(result)} предметов\nРезультат поиска:\n\n"
        find_item = lambda x: items_bd_list_unusual.index(x) if unusual_flag else items_bd_list.index(x)
        buttons = []
        markup = InlineKeyboardMarkup()
        for i in range(10 * page, 10 * (page + 1)):
            if i < len(result):
                mes += f'{i + 1}. {result[i]}\n'
                buttons.append(InlineKeyboardButton(text=result[i], callback_data=base_item.new(item=f'{find_item(result[i])}', unusual=unusual_flag, craft='', select='', status='', type='choice_item'))) # result[i]
        mes += f'\nСтр. {page+1} из {len(result) // 10 + 1}'
        markup.add(*buttons)
        navigation_buttons = []
        if page != 0:
            navigation_buttons.append(create_button('Предыдущая страница', list_menu.new(page=page - 1, type='menu_base', text=text)))
        if page != (len(result) // 10):
            navigation_buttons.append(create_button('Следующая страница', list_menu.new(page=page + 1, type='menu_base', text=text)))
        markup.add(*navigation_buttons)
        if callback == None:
            bot.send_message(message.chat.id, mes, reply_markup=markup)
        else:
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    @bot.callback_query_handler(func=lambda x: list_menu.filter(type='menu_base').check(x))
    @logger.catch()
    def menu_base_search_item_page(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        menu_base_search_item(callback.message, callback, int(list_menu.parse(callback.data)['page']))

    @bot.callback_query_handler(func=lambda x: base_item.filter(type='choice_item').check(x))
    @logger.catch()
    def base_menu_select_item(callback: CallbackQuery):
        if callback.id != -1:
            bot.answer_callback_query(callback.id)
        data = base_item.parse(callback.data)
        item_name = items_bd_list_unusual[int(data['item'])] if data['unusual'] else items_bd_list[int(data['item'])]
        mes = f'Предмет: {item_name}\n\n'
        markup = InlineKeyboardMarkup()
        if 'Unusual' == item_name[:7]:
            print(items_unusual_bd[item_name])
            markup.add(create_button('Добавить эффект', base_item.new(item=data['item'], unusual=data['unusual'], craft='', select='', status='add_effect', type='edit_price')))
            items = items_unusual_bd
            for craft in items_unusual_bd[item_name]:
                mes += f'{craft}:\n'
                if 'Particles' in items_unusual_bd[item_name][craft]:
                    mes += f'\t\tЭффекты:\n'
                    for particl in items_unusual_bd[item_name][craft]['Particles']:
                        mes += (f'\t\t\t\tЭффект: {particl}\n'
                                f'\t\t\t\tЦеник: {items_unusual_bd[item_name][craft]["Particles"][particl]["price"]} {items_unusual_bd[item_name][craft]["Particles"][particl]["currency"]}\n'
                                f'\t\t\t\tЦеник в рублях: {config["currency"][items_unusual_bd[item_name][craft]["Particles"][particl]["currency"]] * items_unusual_bd[item_name][craft]["Particles"][particl]["price"]} ₽\n\n')
                else:
                    mes += (f'\t\tЦеник: {items_unusual_bd[item_name][craft]["price"]} {items_unusual_bd[item_name][craft]["currency"]}\n'
                            f'\t\tЦеник в рублях: {config["currency"][items_unusual_bd[item_name][craft]["currency"]] * items_unusual_bd[item_name][craft]["price"]} ₽\n\n')
        else:
            items = items_bd
            for craft in items_bd[item_name]:
                mes += (f'{craft}:\n'
                        f'\t\tЦеник: {items_bd[item_name][craft]["price"]} {items_bd[item_name][craft]["currency"]}\n'
                        f'\t\tЦеник в рублях: {config["currency"][items_bd[item_name][craft]["currency"]] * items_bd[item_name][craft]["price"]} ₽\n\n')
        if 'Non-Craftable' not in items[item_name]:
            markup.add(create_button('Добавить Non-Craftable', base_item.new(item=data['item'], unusual=data['unusual'], craft='Non-Craftable', select='', status='add_craft', type='add_type')))
        elif 'Craftable' not in items[item_name]:
            markup.add(create_button('Добавить Craftable', base_item.new(item=data['item'], unusual=data['unusual'], craft='Craftable', select='', status='add_craft', type='add_type')))
        buttons = [
            create_button('Изменить ценик', base_item.new(item=data['item'], unusual=data['unusual'], craft='', select='', status='edit_price', type='edit_price')),
            create_button('Удалить предмет', base_item.new(item=data['item'], unusual=data['unusual'], craft='', select='', status='', type='del'))
        ]
        markup.add(*buttons)

        print(markup)
        message_id = ''
        messages = telebot.util.smart_split(mes)
        for i in range(len(messages)):
            if len(messages) == 1:
                bot.edit_message_text(messages[i], callback.message.chat.id, callback.message.message_id, reply_markup=markup)
            else:
                if i == len(messages) - 1:
                    bot.send_message(callback.message.chat.id, messages[i], reply_markup=markup)
                elif i == 0:
                    message_id = bot.edit_message_text(messages[i], callback.message.chat.id, callback.message.message_id).message_id
                    for mark1 in markup.keyboard:
                        for mark2 in mark1:
                            mark2: InlineKeyboardButton = mark2
                            time_data = base_item.parse(mark2.callback_data)
                            time_data['select'] = message_id
                            time_data.pop('@')
                            mark2.callback_data = base_item.new(**time_data)



    @bot.callback_query_handler(func= lambda x: base_item.filter().check(x))
    @logger.catch()
    def base_menu_edit_item(callback: CallbackQuery):
        data = base_item.parse(callback.data)
        item_name = items_bd_list_unusual[int(data['item'])] if data['unusual'] else items_bd_list[int(data['item'])]
        print(base_item.parse(callback.data))

        if data['type'] == 'add_type':
            if data['status'] == 'add_craft':
                if data['unusual']:
                    if data['select']:
                        bot.delete_message(callback.message.chat.id, data['select'])
                    items_unusual_bd[item_name][data['craft']] = {'Particles':{}}
                    data['status'] = 'add_craft_unusual'
                    data['type'] = 'select_effect'
                    data.pop('@')
                    callback.data = base_item.new(**data)
                    base_menu_edit_item(callback)
                    return 0
                else:
                    items_bd[item_name][data['craft']] = {}
            mes = 'Выберите валюту:'
            markup = InlineKeyboardMarkup()
            markup.add(*[create_button('Metal', base_item.new(item=data['item'], unusual=data['unusual'], craft=data['craft'], select='metal', status=data['status'], type='currency')),
                         create_button('Keys', base_item.new(item=data['item'], unusual=data['unusual'], craft=data['craft'], select='keys', status=data['status'], type='currency'))])
            markup.add(create_button('Отмена', base_item.new(item=data['item'], unusual=data['unusual'], craft=data['craft'], select='craft', status=data['status'], type='cancel')))
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)
        elif data['type'] == 'currency':
            if data['unusual']:
                effects = list(items_unusual_bd[item_name][data['craft']]['Particles'])
                items_unusual_bd[item_name][data['craft']]['Particles'][effects[int(data['unusual'])]]['new_currency'] = data['select']
            else:
                items_bd[item_name][data['craft']]['new_currency'] = data['select']
            bot.edit_message_text('Пришлите ценик (0 для отмены):', callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, base_menu_item_send, 'currency', callback)
        elif data['type'] == 'edit_price':
            markup = InlineKeyboardMarkup()
            buttons = []
            crafts = []
            unusual_flag = 'add_type'
            if data['unusual']:
                if data['select']:
                    bot.delete_message(callback.message.chat.id, data['select'])
                unusual_flag = 'select_effect'
                for craft in items_unusual_bd[item_name]:
                    crafts.append(craft)
                    buttons.append(create_button(craft, base_item.new(item=data['item'], unusual=data['unusual'], craft=craft, select='', status=data['status'], type='select_effect')))
            else:
                for craft in items_bd[item_name]:
                    crafts.append(craft)
                    buttons.append(create_button(craft, base_item.new(item=data['item'], unusual=data['unusual'], craft=craft, select='', status=data['status'], type='add_type')))
            if len(crafts) >= 2:
                mes = 'Выберите тип:'
                markup.add(*buttons)
                markup.add(create_button('Отмена', base_item.new(item=data['item'], unusual=data['unusual'],
                                                                 craft='', select='',
                                                                 status=data['status'], type='cancel')))
                bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)
            else:
                craft = crafts[0]
                callback.data = base_item.new(item=data['item'], unusual=data['unusual'], craft=craft, select='', status=data['status'], type=unusual_flag)
                base_menu_edit_item(callback)
        elif data['type'] == 'cancel':
            if data['status'] == 'add_craft':
                items_bd[item_name].pop(data['craft'])
            elif data['status'] == 'add_effect':
                effects = list(items_unusual_bd[item_name][data['craft']]['Particles'])
                items_unusual_bd[item_name][data['craft']]['Particles'].pop(effects[int(data['unusual'])])
            elif data['status'] == 'add_craft_unusual':
                items_unusual_bd[item_name].pop(data['craft'])
            base_menu_select_item(callback)
            return 0
        elif data['type'] == 'select_effect':
            if data['status'] == 'edit_price':
                mes = 'Пришлите название эффекта, такой же как в базе (0 для отмены):'
            elif data['status'] == 'add_effect' or data['status'] == 'add_craft_unusual':
                mes = 'Пришлите название эффекта (0 для отмены):'
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id)
            bot.register_next_step_handler(callback.message, base_menu_item_send, 'select_effect', callback)

        if callback.id != -1:
            bot.answer_callback_query(callback.id)

    @logger.catch()
    def base_menu_item_send(message: Message, type: str, callback: CallbackQuery):
        data = base_item.parse(callback.data)
        callback.id = -1
        item_name = items_bd_list_unusual[int(data['item'])] if data['unusual'] else items_bd_list[int(data['item'])]
        if data['unusual']:
            effects = list(items_unusual_bd[item_name][data['craft']]['Particles'])
        if type == 'currency':
            if message.text == '0':
                if data['status'] == 'add_craft':
                    items_bd[item_name].pop(data['craft'])
                elif data['status'] == 'add_effect':
                    items_unusual_bd[item_name][data['craft']]['Particles'].pop(effects[int(data['unusual'])])
                elif data['status'] == 'add_craft_unusual':
                    items_unusual_bd[item_name].pop(data['craft'])
                else:
                    if data['unusual']:
                        items_unusual_bd[item_name][data['craft']]['Particles'][effects[int(data['unusual'])]].pop('new_currency')
                    else:
                        items_bd[item_name][data['craft']].pop('new_currency')
            else:
                try:
                    price = float(message.text)
                    if data['unusual']:
                        items_unusual_bd[item_name][data['craft']]['Particles'][effects[int(data['unusual'])]]['price'] = price
                        items_unusual_bd[item_name][data['craft']]['Particles'][effects[int(data['unusual'])]]['currency'] = items_unusual_bd[item_name][data['craft']]['Particles'][effects[int(data['unusual'])]]['new_currency']
                        items_unusual_bd[item_name][data['craft']]['Particles'][effects[int(data['unusual'])]].pop('new_currency')
                    else:
                        items_bd[item_name][data['craft']]['price'] = price
                        items_bd[item_name][data['craft']]['currency'] = items_bd[item_name][data['craft']]['new_currency']
                        items_bd[item_name][data['craft']].pop('new_currency')
                except:
                    bot.send_message(message.chat.id, 'Неверный формат!')
                    bot.send_message(message.chat.id, 'Пришлите ценик (0 для отмены):')
                    bot.register_next_step_handler(message, base_menu_item_send, 'currency', callback)
                    return 0
            callback.message = bot.send_message(message.chat.id, 'Пум...')
            callback.data = base_item.new(item=data['item'], unusual=data['unusual'], craft=data['craft'], select='', status='', type='choice_item')
            base_menu_select_item(callback)
        elif type == 'select_effect':
            if message.text == '0':
                if data['status'] == 'add_craft_unusual':
                    items_unusual_bd[item_name].pop(data['craft'])
                callback.message = bot.send_message(message.chat.id, 'Пум...')
                callback.data = base_item.new(item=data['item'], unusual=data['unusual'], craft=data['craft'],select='', status='', type='choice_item')
                base_menu_select_item(callback)
                return 0
            if data['status'] == 'edit_price':
                if message.text not in effects:
                    bot.send_message(callback.message.chat.id,'Эффекта нету в базе!')
                    bot.send_message(callback.message.chat.id, 'Пришлите название эффекта, такой же как в базе (0 для отмены):')
                    bot.register_next_step_handler(callback.message, base_menu_item_send, 'select_effect', callback)
                    return 0
                callback.message = bot.send_message(message.chat.id, 'Пум...')
                callback.data = base_item.new(item=data['item'], unusual=effects.index(message.text), craft=data['craft'],
                                              select='', status=data['status'], type='add_type')
                base_menu_edit_item(callback)
            elif data['status'] == 'add_effect' or data['status'] == 'add_craft_unusual':
                if message.text not in effects:
                    effect_id = len(list(items_unusual_bd[item_name][data['craft']]['Particles']))
                    items_unusual_bd[item_name][data['craft']]['Particles'][message.text] = {}
                    callback.data = base_item.new(item=data['item'], unusual=effect_id,
                                                  craft=data['craft'],
                                                  select='', status=data['status'], type='add_type')
                    callback.message = bot.send_message(message.chat.id, 'Пум...')
                    base_menu_edit_item(callback)
                else:
                    bot.send_message(callback.message.chat.id, 'Эффект есть в базе!')
                    bot.send_message(callback.message.chat.id, 'Пришлите название эффекта (0 для отмены):')
                    bot.register_next_step_handler(callback.message, base_menu_item_send, 'select_effect', callback)
                    return 0

    @bot.callback_query_handler(func= lambda x: item_message.filter().check(x))
    def item_mes(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data_callback = item_message.parse(callback.data)
        print(data_callback)


    logger.debug('Start handlers telegram bot')
