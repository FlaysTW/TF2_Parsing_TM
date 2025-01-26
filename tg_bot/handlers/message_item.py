from telebot import TeleBot
from telebot.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils.loging import logger
from tg_bot.callbacks_data import item_message
from parsing import TM_Parsing
from utils.loading_data import items_bd_list, items_bd_list_unusual, items_cache, future
from tg_bot.utils import cancel
from utils.config import config
import json
from telebot.util import antiflood

future_add = [0]

def run(bot: TeleBot, tm: TM_Parsing, bot_menu: TeleBot):
    @bot.callback_query_handler(func= lambda x: item_message.filter(type='buy').check(x))
    @logger.catch()
    def buy_item(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = item_message.parse(callback.data)
        classid = data['classid']
        instanceid = data['instanceid']
        price = data['price']
        tm.buy_item(classid, instanceid, price)

    @bot.callback_query_handler(func= lambda x: item_message.filter(type='del').check(x))
    @logger.catch()
    def delete_item_in_cache(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        data = item_message.parse(callback.data)
        try:
            name = items_cache.pop(f'{data["classid"]}-{data["instanceid"]}')
            mes = callback.message
            mes.text = 'УДАЛЕН ИЗ КЭША!\n' + mes.text
            bot.edit_message_text(mes.text, mes.chat.id, mes.message_id)
            bot_menu.send_message(callback.message.chat.id, f"Предмет <a href='https://t.me/c/{str(callback.message.chat.id)[4:]}/{callback.message.message_thread_id}/{callback.message.message_id}'>{name['name']}</a> успешно удален из кэша!", parse_mode='HTML')
        except:
            bot_menu.send_message(callback.message.chat.id, f"<a href='https://t.me/c/{str(callback.message.chat.id)[4:]}/{callback.message.message_thread_id}/{callback.message.message_id}'>Предмет</a> уже удален из кэша!", parse_mode='HTML')

    @bot.callback_query_handler(func=lambda x: item_message.filter(type='pnb').check(x))
    @logger.catch()
    def bot_accept_future(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        future_add[0] = {'notification': {}, 'autobuy': {}}
        callback.id = -1
        items_for_future(callback)

    @bot_menu.callback_query_handler(func=lambda x: item_message.filter(type='pnb').check(x))
    @logger.catch()
    def items_for_future(callback: CallbackQuery):
        if callback.id != -1:
            future_add[0] = {'notification':{}, 'autobuy':{}}
            bot_menu.answer_callback_query(callback.id)
        data = item_message.parse(callback.data)
        data.pop('@')
        markup = InlineKeyboardMarkup()
        item = items_cache[f'{data["classid"]}-{data["instanceid"]}']
        flag = False
        mes = f"Настройка ПНБ для предмета <a href='https://t.me/c/{str(callback.message.chat.id)[4:]}/{item['message']['message_thread_id']}/{item['message']['message_id']}'>{item['name']} {data['classid']}-{data['instanceid']}</a>"
        if f'{data["classid"]}-{data["instanceid"]}' not in future_add[0]['notification']:
            data['type'] = 'not'
            markup.add(InlineKeyboardButton('Прислать если цена понизится',callback_data=item_message.new(**data)))
        else:
            flag = True
            mes += '\n\n' + 'Уведомление когда цена будет равна или ниже - ' + str(round(future_add[0]['notification'][f'{data["classid"]}-{data["instanceid"]}']['procent'] / 100,2)) + ' ₽'

        if f'{data["classid"]}-{data["instanceid"]}' not in future_add[0]['autobuy']:
            data['type'] = 'buyo'
            markup.add(InlineKeyboardButton('Купить если цена понизится', callback_data=item_message.new(**data)))
        else:
            flag = True
            mes += '\n\n' + 'Будет куплен когда цена будет равна или ниже - ' + str(
                round(future_add[0]['autobuy'][f'{data["classid"]}-{data["instanceid"]}']['procent'] / 100,2)) + ' ₽'
        if flag:
            data['type'] = 'ready'
            markup.add(InlineKeyboardButton('Сохранить', callback_data=item_message.new(**data)))
        bot_menu.send_message(callback.message.chat.id, mes, parse_mode='HTML', reply_markup=markup)
        # bot.send_message(callback.message.chat.id, 'Пришлите на сколько % должна понизится цена от 1 до 100 (0 для отмены):')
        # bot.register_next_step_handler(callback.message, items_for_future_message, data["classid"], data["instanceid"], data['price'], typ)

    @bot_menu.callback_query_handler(func=lambda x: item_message.filter(type='not').check(x) or item_message.filter(type='buyo').check(x) or item_message.filter(type='ready').check(x))
    @logger.catch()
    def items_for_future_callback(callback: CallbackQuery):
        bot_menu.answer_callback_query(callback.id)
        data = item_message.parse(callback.data)
        if data['type'] == 'ready':
            if f'{data["classid"]}-{data["instanceid"]}' in future_add[0]['notification']:
                future['notification'][f'{data["classid"]}-{data["instanceid"]}'] = future_add[0]['notification'][f'{data["classid"]}-{data["instanceid"]}']
            if f'{data["classid"]}-{data["instanceid"]}' in future_add[0]['autobuy']:
                future['autobuy'][f'{data["classid"]}-{data["instanceid"]}'] = future_add[0]['autobuy'][f'{data["classid"]}-{data["instanceid"]}']
            future_add[0] = 0
            item = items_cache.pop(f'{data["classid"]}-{data["instanceid"]}')
            bot.edit_message_text('УДАЛЕН ИЗ КЭША!\n' + item['message']['text'], item['message']['chat']['id'], item['message']['message_id'])
            bot_menu.edit_message_text(callback.message.text, callback.message.chat.id, callback.message.message_id)
            bot_menu.send_message(callback.message.chat.id, 'Готово')
        else:
            mes = ''
            if data['type'] == 'not':
                typ = 'notification'
                mes += 'Настройка ПНБ уведомления\n'
            elif data['type'] == 'buyo':
                typ = 'autobuy'
                mes += 'Настройка ПНБ автопокупка\n'
            mes += 'Пришлите на сколько % должна понизится цена от 1 до 100 (0 для отмены):'
            bot_menu.send_message(callback.message.chat.id, mes)
            bot_menu.register_next_step_handler(callback.message, items_for_future_message, callback, data['classid'], data['instanceid'], data['price'], typ)

    @logger.catch()
    def items_for_future_message(message: Message, callback: CallbackQuery, classid, instanceid, price, typ):
        if message.text == '0':
            future_add[0] = 0
            cancel(bot, message.chat.id)
        else:
            try:
                procent = int(message.text)
                if procent not in [i for i in range(1, 101)]:
                    a = 10 / 0
                future_add[0][typ][f'{classid}-{instanceid}'] = {'procent' : float(price) * ((100 - procent) / 100), 'name': items_cache[f'{classid}-{instanceid}']['name'], 'old_price': float(price)}
                callback.id = -1
                items_for_future(callback)
            except:
                bot_menu.send_message(message.chat.id, 'Неправильный формат!')
                bot_menu.send_message(message.chat.id, 'Пришлите на сколько % должна понизится цена от 1 до 100 (0 для отмены):')
                bot_menu.register_next_step_handler(message, items_for_future_message, classid, instanceid, typ)


    @bot.callback_query_handler(func=lambda x: item_message.filter(type='add_BL_AB').check(x))
    @logger.catch()
    def add_blacklist_autobuy(callback: CallbackQuery):
        bot.answer_callback_query(callback.id)
        mes_text = callback.message.text
        raw_name = mes_text.split('\n')[1].split('предмета: ')[1].strip()
        name = raw_name.lower()
        if name not in config['autobuy_blacklist']:
            config['autobuy_blacklist'].append(name)
            with open('./data/config.json', 'w', encoding='utf-8') as file:
                json.dump(config, file, ensure_ascii=False, indent=4)
            bot_menu.send_message(callback.message.chat.id, f'"{raw_name}" добавлен в чс для автопокупки!')
        else:
            bot_menu.send_message(callback.message.chat.id, f'"{raw_name}" уже находится в чс для автопокупки!')

    @bot.callback_query_handler(func=lambda x: item_message.filter().check(x))
    @logger.catch()
    def test(callback: CallbackQuery):
        print(callback.data)
