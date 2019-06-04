#!/usr/bin/python3.6
# coding: utf8
import time
import datetime

import sys #required because files in other folder
sys.path.append('./classes/')
from bot import Bot
from dbhelper import DBHelper
from dialogue_bot import DialogueBot

import logging
import pandas as pd

Bot = Bot()
db = DBHelper()

def main(chat_id=None):
    ## main job
    db.setup()
    last_update_id = None

    # set up logging
    logging.basicConfig()

    while True:
        try:
            ## get updates
            # add upkeep
            created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            db.add_upkeep(created_at, 'main')
            updates = Bot.get_updates(last_update_id)
            ## main job
            if len(updates["result"]) > 0:
                start_time = time.time()
                last_update_id = Bot.get_last_update_id(updates) + 1
                # update_elements holds the user's initial message
                update_elements = Bot.extract_updates(updates, start_time)
                Bot.handle_updates(update_elements["first_name"], update_elements["chat_id"], update_elements["intent"], update_elements["message"], start_time)

        except Exception as e:
            print(e)
            # add error to error table - better would be queue
            created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            context = 'nad_coachee'
            db.add_error(created_at, 'main', context, str(e))

        time.sleep(0.5)
        sys.stdout.write('.'); sys.stdout.flush()

if __name__ == '__main__':
    main()
