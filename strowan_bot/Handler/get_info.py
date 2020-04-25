import datetime
import pandas as pd

import sys #required because files in parent folder
sys.path.append('..')
import config
from sqlalchemy import *
engine = create_engine(config.POSTGRES)
metadata = MetaData(engine)
conn = engine.connect()


def get_fast_duration(difference):
    try:
        seconds_in_day = 24 * 60 * 60
        fast_duration_hours = divmod(difference.days * seconds_in_day + difference.seconds, 3600)[0]
        fast_duration_mins = divmod(difference.days * seconds_in_day + difference.seconds, 60)[0] - fast_duration_hours*60
        fast_duration = f"{fast_duration_hours} Stunden und {fast_duration_mins} Minuten"
    except:
        fast_duration = '0 Stunden und 0 Minuten'
    return fast_duration


def get_active_fasts():
    #### get active fasts
    txt = f"""
            SELECT
                COUNT(s.platform_user_id) AS cnt_user
            FROM
                (
                -- get last created_at related to either fast start or end
                SELECT 
                    us.platform_user_id
                    , max(u.created_at) AS created_at
                FROM updates u
                JOIN users us
                    ON u.platform_chat_id = us.platform_user_id
                WHERE 
                    u.key_value in ('fast_start_text', 'fasten_end_text')
                GROUP BY 1
                ) s
            -- only keep those users with fast start as last value
            JOIN updates u
                ON (s.platform_user_id = u.platform_chat_id
                    AND s.created_at = u.created_at
                    AND u.key_value = 'fast_start_text')
            """
    data = pd.read_sql_query(txt, conn)
    return data

def get_active_fasts_txt(cnt_user):
    if cnt_user == 1:
        txt = f"Aktuell fastet {cnt_user} Mitglied."
    else:
        txt = f"Aktuell fasten {cnt_user} Mitglieder."

    return txt


def get_user_info_fast(user_id):
    #### get active fasts
    txt = f"""
            -- get last created_at related to either fast start or end
            SELECT 
                us.platform_user_id
                , u.key_value
                , max(u.created_at) AS created_at
            FROM updates u
            JOIN users us
                ON u.platform_chat_id = us.platform_user_id
            WHERE 
                u.platform_chat_id = {user_id} 
                -- important: use this to get key value from bot msg, not user msg !
                AND u.platform_chat_id != u.platform_user_id
                AND u.key_value in ('fast_start_text', 'fasten_end_text')
            GROUP BY 1, 2
            """
    data = pd.read_sql_query(txt, conn)
    return data

def get_user_info_fast_txt(data):
    fast_status = 'not_fasting'
    # check if user has ever fasted:
    if len(data) > 0:
        # check, whether the user started or ended a fast last
        temp = data[data.created_at == data.created_at.max()].reset_index(drop=True)
        # if user started a fast last, calculate fast_duration
        if temp.key_value.values[0] == 'fast_start_text':
            difference = datetime.datetime.now() - temp.created_at[0]
            fast_status = 'fasting'
        else:
            difference = None
        fast_duration = get_fast_duration(difference)
    # if user never fasted:
    else:
        fast_duration = '0 Stunden und 0 Minuten'
    return fast_duration, fast_status    



if __name__ == '__main__':
    data = get_active_fasts()
    txt = get_active_fasts_txt(data["cnt_user"][0])
    print(txt)

    user_id = config.TEST_USER
    data = get_user_info_fast(user_id)
    txt = get_user_info_fast_txt(data)
    print(txt)