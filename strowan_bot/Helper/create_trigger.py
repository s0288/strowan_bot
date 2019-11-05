import sys #required because files in parent folder
sys.path.append('../Handler')
from db_bot import DBBot

import datetime

DBBot = DBBot()

active_users = DBBot.get_active_users()

trigger_value = '/challenge'
trigger_day = 'Wed'
trigger_time = '15:00'
for user in active_users:
    platform_user_id = user[0]
    platform_chat_id = platform_user_id

    # check if already there or add
    if DBBot.check_triggers(platform_user_id, platform_chat_id, trigger_value, trigger_day, trigger_time) == 0:
        received_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        created_at = received_at
        DBBot.add_trigger(platform_user_id, platform_chat_id, trigger_value, trigger_time, trigger_day, created_at, received_at)
        print('trigger for {} added'.format(trigger_value))

## add later: remove trigger
# DBBot.delete_from_triggers(user_id, trigger_value, trigger_day, created_at)
# print('removed trigger')