from telebot.callback_data import CallbackData

menu_page = CallbackData('page', prefix='menu')
list_menu = CallbackData('page', 'type', 'text', prefix='list')
base_item = CallbackData('type', 'select', 'item', 'unusual', 'status', 'craft', prefix='bi')
add_item_select = CallbackData('select', 'type', prefix='additem')
item_message = CallbackData('classid', 'instanceid', 'type', prefix='im')
settings_menu = CallbackData('type', 'dump', prefix='st')