import logging

from .arguments import get_args

args = get_args()

# clear log file
file = open('debug.log','w')
file.close()

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger('kemono-dl')
logger.setLevel(args['verbose'])

file_format = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s')
stream_format = logging.Formatter('%(levelname)s: %(message)s')

file_handler = logging.FileHandler('debug.log', encoding="utf-16")
file_handler.setFormatter(file_format)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(stream_format)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)