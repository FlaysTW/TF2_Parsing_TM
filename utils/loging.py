from loguru import logger
import sys

def check(x):
    if 'id' in x['extra']:
        if 'tg' in x['extra']['id']:
            return True
        return False
    return False

logger.remove()
logger.add(sink=sys.stdout)
logger.add(sink='./logs/log.log', rotation='1 day')