#!/usr/bin/python3.6
# coding: utf8

import pandas as pd

import sys #required because files in parent folder
sys.path.append('../')
import config

from sqlalchemy import create_engine, MetaData
engine = create_engine(config.POSTGRES)
metadata = MetaData(engine)
conn = engine.connect()


# retrieve activity values
def track_activity(periods):
    for period in periods:
        stmt = f"""
                SELECT 
                    u.first_name,  
                    CASE WHEN u.created_at > NOW() - interval '{period} weeks' THEN 1 ELSE 0 END AS new_user,
                    COUNT(k.key_value) FILTER(WHERE k.key_value = 'user_photo') AS cnt_imgs,
                    COUNT(k.key_value) FILTER(WHERE k.key_value = 'weight_value_float') AS cnt_weight,
                    COUNT(k.key_value) FILTER(WHERE k.key_value = 'past_week_text') AS cnt_assessment,
                    COUNT(up.message) FILTER(WHERE up.bot_command = "bot_command" AND up.intent = '/profil') AS cnt_profil,
                    COUNT(up.message) FILTER(WHERE up.bot_command = "bot_command" AND up.intent = '/rezepte') AS cnt_rezepte,
                    COUNT(up.message) FILTER(WHERE up.bot_command = "bot_command" AND up.intent = '/fasten') AS cnt_fast,
                    COUNT(up.message) FILTER(WHERE up.bot_command = "bot_command" AND up.intent = '/nachtragen') AS cnt_nachtragen,
                    COUNT(up.message) FILTER(WHERE up.bot_command = "bot_command" AND up.intent = '/befehle') AS cnt_befehle
                FROM updates up
                LEFT JOIN key_values k ON
                    up.platform_user_id = k.platform_user_id AND up.key_value = k.key_value AND up.created_at = k.created_at
                JOIN users u ON 
                    up.platform_user_id = u.platform_user_id
                -- only consider values from last week
                WHERE up.created_at > NOW() - interval '{period} weeks'
                GROUP BY 1, 2
                """
        df = pd.read_sql_query(stmt, conn)
        print(f'--- Lookback period: {period} weeks')
        print('')
        print(df)
        print('')
        print('')

# get activity values
periods = [1, 4, 12]
track_activity(periods)