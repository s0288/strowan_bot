import pandas as pd

import sys #required because files in parent folder
sys.path.append('..')
import config
from sqlalchemy import *
engine = create_engine(config.POSTGRES)
metadata = MetaData(engine)
conn = engine.connect()

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
        txt = f"Aktuell fastet {cnt_user} Mitglied"
    else:
        txt = f"Aktuell fasten {cnt_user} Mitglieder"

    return txt


data = get_active_fasts()
txt = get_active_fasts_txt(data["cnt_user"][0])

print(txt)