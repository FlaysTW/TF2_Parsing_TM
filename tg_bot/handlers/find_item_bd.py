import telebot
from telebot import TeleBot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from tg_bot.callbacks_data import menu_page, list_menu, base_item
from utils.loging import logger
from utils.loading_data import items_bd, items_bd_list, items_bd_list_unusual, items_unusual_bd
from tg_bot.utils import create_button
from utils.config import config

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

def run(bot: TeleBot, tm):
    # Регистратор название предмета для поиска
    @bot.callback_query_handler(func=lambda x: menu_page.filter(page='find_item').check(x))
    @logger.catch()
    def menu_base_find_item(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        bot.edit_message_text('Пришлите название предмета', callback.message.chat.id, callback.message.message_id)
        bot.register_next_step_handler_by_chat_id(callback.message.chat.id, menu_base_search_item)

    # Результат поиска
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
                buttons.append(InlineKeyboardButton(text=result[i],
                                                    callback_data=base_item.new(item=f'{find_item(result[i])}',
                                                                                unusual=unusual_flag, craft='',
                                                                                select='', status='',
                                                                                type='choice_item')))  # result[i]
        mes += f'\nСтр. {page + 1} из {len(result) // 10 + 1}'
        markup.add(*buttons)
        navigation_buttons = []
        if page != 0:
            navigation_buttons.append(
                create_button('Предыдущая страница', list_menu.new(page=page - 1, type='menu_base', text=text)))
        if page != (len(result) // 10):
            navigation_buttons.append(
                create_button('Следующая страница', list_menu.new(page=page + 1, type='menu_base', text=text)))
        markup.add(*navigation_buttons)
        if callback == None:
            bot.send_message(message.chat.id, mes, reply_markup=markup)
        else:
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)

    # Перелистование результат
    @bot.callback_query_handler(func=lambda x: list_menu.filter(type='menu_base').check(x))
    @logger.catch()
    def menu_base_search_item_page(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        menu_base_search_item(callback.message, callback, int(list_menu.parse(callback.data)['page']))

    # Вывод предмета
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
            markup.add(create_button('Добавить эффект',
                                     base_item.new(item=data['item'], unusual=data['unusual'], craft='', select='',
                                                   status='add_effect', type='edit_price')))
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
                    mes += (
                        f'\t\tЦеник: {items_unusual_bd[item_name][craft]["price"]} {items_unusual_bd[item_name][craft]["currency"]}\n'
                        f'\t\tЦеник в рублях: {config["currency"][items_unusual_bd[item_name][craft]["currency"]] * items_unusual_bd[item_name][craft]["price"]} ₽\n\n')
        else:
            items = items_bd
            for craft in items_bd[item_name]:
                mes += (f'{craft}:\n'
                        f'\t\tЦеник: {items_bd[item_name][craft]["price"]} {items_bd[item_name][craft]["currency"]}\n'
                        f'\t\tЦеник в рублях: {config["currency"][items_bd[item_name][craft]["currency"]] * items_bd[item_name][craft]["price"]} ₽\n\n')
        if 'Non-Craftable' not in items[item_name]:
            markup.add(create_button('Добавить Non-Craftable',
                                     base_item.new(item=data['item'], unusual=data['unusual'], craft='Non-Craftable',
                                                   select='', status='add_craft', type='add_type')))
        elif 'Craftable' not in items[item_name]:
            markup.add(create_button('Добавить Craftable',
                                     base_item.new(item=data['item'], unusual=data['unusual'], craft='Craftable',
                                                   select='', status='add_craft', type='add_type')))
        buttons = [
            create_button('Изменить ценик',
                          base_item.new(item=data['item'], unusual=data['unusual'], craft='', select='',
                                        status='edit_price', type='edit_price')),
            create_button('Удалить предмет',
                          base_item.new(item=data['item'], unusual=data['unusual'], craft='', select='', status='',
                                        type='del'))
        ]
        markup.add(*buttons)
        message_id = ''
        messages = telebot.util.smart_split(mes)
        for i in range(len(messages)):
            if len(messages) == 1:
                bot.edit_message_text(messages[i], callback.message.chat.id, callback.message.message_id,
                                      reply_markup=markup)
            else:
                if i == len(messages) - 1:
                    bot.send_message(callback.message.chat.id, messages[i], reply_markup=markup)
                elif i == 0:
                    message_id = bot.edit_message_text(messages[i], callback.message.chat.id,
                                                       callback.message.message_id).message_id
                    for mark1 in markup.keyboard:
                        for mark2 in mark1:
                            mark2: InlineKeyboardButton = mark2
                            time_data = base_item.parse(mark2.callback_data)
                            time_data['select'] = message_id
                            time_data.pop('@')
                            mark2.callback_data = base_item.new(**time_data)

    # Каллбак регистратор
    @bot.callback_query_handler(func=lambda x: base_item.filter().check(x))
    @logger.catch()
    def base_menu_edit_item(callback: CallbackQuery):
        data = base_item.parse(callback.data)
        item_name = items_bd_list_unusual[int(data['item'])] if data['unusual'] else items_bd_list[int(data['item'])]

        if data['type'] == 'add_type':
            if data['status'] == 'add_craft':
                if data['unusual']:
                    if data['select']:
                        bot.delete_message(callback.message.chat.id, data['select'])
                    items_unusual_bd[item_name][data['craft']] = {'Particles': {}}
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
            markup.add(*[create_button('Metal',
                                       base_item.new(item=data['item'], unusual=data['unusual'], craft=data['craft'],
                                                     select='metal', status=data['status'], type='currency')),
                         create_button('Keys',
                                       base_item.new(item=data['item'], unusual=data['unusual'], craft=data['craft'],
                                                     select='keys', status=data['status'], type='currency'))])
            markup.add(create_button('Отмена',
                                     base_item.new(item=data['item'], unusual=data['unusual'], craft=data['craft'],
                                                   select='craft', status=data['status'], type='cancel')))
            bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)
        elif data['type'] == 'currency':
            if data['unusual']:
                effects = list(items_unusual_bd[item_name][data['craft']]['Particles'])
                items_unusual_bd[item_name][data['craft']]['Particles'][effects[int(data['unusual'])]]['new_currency'] = \
                data['select']
            else:
                items_bd[item_name][data['craft']]['new_currency'] = data['select']
            bot.edit_message_text('Пришлите ценик (0 для отмены):', callback.message.chat.id,
                                  callback.message.message_id)
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
                    buttons.append(create_button(craft,
                                                 base_item.new(item=data['item'], unusual=data['unusual'], craft=craft,
                                                               select='', status=data['status'], type='select_effect')))
            else:
                for craft in items_bd[item_name]:
                    crafts.append(craft)
                    buttons.append(create_button(craft,
                                                 base_item.new(item=data['item'], unusual=data['unusual'], craft=craft,
                                                               select='', status=data['status'], type='add_type')))
            if len(crafts) >= 2:
                mes = 'Выберите тип:'
                markup.add(*buttons)
                markup.add(create_button('Отмена', base_item.new(item=data['item'], unusual=data['unusual'],
                                                                 craft='', select='',
                                                                 status=data['status'], type='cancel')))
                bot.edit_message_text(mes, callback.message.chat.id, callback.message.message_id, reply_markup=markup)
            else:
                craft = crafts[0]
                callback.data = base_item.new(item=data['item'], unusual=data['unusual'], craft=craft, select='',
                                              status=data['status'], type=unusual_flag)
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

    # Регистратор сообщений
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
                        items_unusual_bd[item_name][data['craft']]['Particles'][effects[int(data['unusual'])]].pop(
                            'new_currency')
                    else:
                        items_bd[item_name][data['craft']].pop('new_currency')
            else:
                try:
                    price = float(message.text)
                    if data['unusual']:
                        items_unusual_bd[item_name][data['craft']]['Particles'][effects[int(data['unusual'])]][
                            'price'] = price
                        items_unusual_bd[item_name][data['craft']]['Particles'][effects[int(data['unusual'])]][
                            'currency'] = \
                        items_unusual_bd[item_name][data['craft']]['Particles'][effects[int(data['unusual'])]][
                            'new_currency']
                        items_unusual_bd[item_name][data['craft']]['Particles'][effects[int(data['unusual'])]].pop(
                            'new_currency')
                    else:
                        items_bd[item_name][data['craft']]['price'] = price
                        items_bd[item_name][data['craft']]['currency'] = items_bd[item_name][data['craft']][
                            'new_currency']
                        items_bd[item_name][data['craft']].pop('new_currency')
                except:
                    bot.send_message(message.chat.id, 'Неверный формат!')
                    bot.send_message(message.chat.id, 'Пришлите ценик (0 для отмены):')
                    bot.register_next_step_handler(message, base_menu_item_send, 'currency', callback)
                    return 0
            callback.message = bot.send_message(message.chat.id, 'Пум...')
            callback.data = base_item.new(item=data['item'], unusual=data['unusual'], craft=data['craft'], select='',
                                          status='', type='choice_item')
            base_menu_select_item(callback)
        elif type == 'select_effect':
            if message.text == '0':
                if data['status'] == 'add_craft_unusual':
                    items_unusual_bd[item_name].pop(data['craft'])
                callback.message = bot.send_message(message.chat.id, 'Пум...')
                callback.data = base_item.new(item=data['item'], unusual=data['unusual'], craft=data['craft'],
                                              select='', status='', type='choice_item')
                base_menu_select_item(callback)
                return 0
            if data['status'] == 'edit_price':
                if message.text not in effects:
                    bot.send_message(callback.message.chat.id, 'Эффекта нету в базе!')
                    bot.send_message(callback.message.chat.id,
                                     'Пришлите название эффекта, такой же как в базе (0 для отмены):')
                    bot.register_next_step_handler(callback.message, base_menu_item_send, 'select_effect', callback)
                    return 0
                callback.message = bot.send_message(message.chat.id, 'Пум...')
                callback.data = base_item.new(item=data['item'], unusual=effects.index(message.text),
                                              craft=data['craft'],
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