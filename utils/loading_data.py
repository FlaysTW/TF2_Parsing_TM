import json

with open('./items/items.json', 'r', encoding='UTF-8') as file:
    items_bd = json.load(file)

with open('./items/unusual_items.json', 'r', encoding='UTF-8') as file:
    items_unusual_bd = json.load(file)

items_bd_list = [x for x in items_bd]

items_bd_list_unusual = [x for x in items_unusual_bd]

with open('./items/cache.json', 'r', encoding='utf-8') as file:
    items_cache = json.load(file)