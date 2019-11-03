import sys #required because files in other folder
sys.path.append('../Telegram/')
from bot import Bot

Bot = Bot()

Bot.trigger_message('/challenge', 415604082)
