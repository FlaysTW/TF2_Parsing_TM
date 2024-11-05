import json

with open('./items.json', 'r', encoding='UTF-8') as file:
    items_bd = json.load(file)

items_bd_list = [x for x in items_bd if 'Unusual' != x]

items_bd_list_unusual = [x for x in items_bd['Unusual']]