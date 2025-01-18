from loguru import logger
import sys

def check_not_items(x):
    if 'id' in x['extra']:
        return False
    else:
        return True

logger_list = {}

def create_logger_item(id):
    def check(x):
        if 'id' in x['extra']:
            if id == x['extra']['id']:
                return True
            return False
        return False
    if id not in logger_list:
        logger_id = logger.add(sink=f'./logs/items/{id}.log', filter=check)
        logger_list[id] = logger_id
        return logger_id
    else:
        return logger_list[id]

def delete_logger_item(id):
    logger_id = logger_list.pop(id)
    logger.remove(logger_id)

def check_logs():
    print(len(logger_list))

logger.remove()
logger.add(sink=sys.stdout, filter=check_not_items)
logger.add(sink='./logs/log.log', rotation='1 day', filter=check_not_items)