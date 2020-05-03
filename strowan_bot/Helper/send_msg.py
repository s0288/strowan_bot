#!/usr/bin/python3.6
# coding: utf8

############################################################################################
# General purpose: Trigger msgs to users
# Specific purpose: Send progress plots to all users that started a fast within last 7 days
############################################################################################

import datetime
import pandas as pd

import sys #required because files in other folder
sys.path.append('..')
import config

sys.path.append('../Telegram')
from bot import Bot

sys.path.append('../Handler/')
from db_bot import DBBot
from dialogue_bot import DialogueBot
from fast_overview import create_progress_plot, get_fasting_data, get_output_location

import sys #required because files in parent folder
sys.path.append('..')
import config
from sqlalchemy import *
engine = create_engine(config.POSTGRES)
metadata = MetaData(engine)
conn = engine.connect()

Bot = Bot()

def get_last_weeks_fasting_users():
    #### get active fasts
    txt = f"""
            SELECT
                s.platform_user_id
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
                    u.key_value in ('fast_start_text')
                    AND us.platform_user_id NOT IN ({config.CORRECT_USER_1}, {config.CORRECT_USER_2}, {config.CORRECT_USER_3})
                GROUP BY 1
                ) s
            -- only keep those users with fast start as last value within the last 7 days
            JOIN updates u
                ON (s.platform_user_id = u.platform_chat_id
                    AND s.created_at = u.created_at
                    AND u.key_value = 'fast_start_text'
                    AND u.created_at > current_date - interval '7 days')
            """
    data = pd.read_sql_query(txt, conn)
    return data


if __name__ == '__main__':

    # only trigger on Sundays
    if datetime.datetime.today().weekday() == 6:
        # get users that fasted within last 7 days
        chat_ids = get_last_weeks_fasting_users()
        # loop through users
        for i in chat_ids.iterrows():
            try:
                chat_id = i[1]["platform_user_id"]
                # get data to create progress plot
                df_fast = get_fasting_data(chat_id)
                output_file_location = get_output_location(chat_id, plot_type='progress')
                # create progress plot
                create_progress_plot(df_fast, output_file_location)

                # prepare msg
                img = f"http://s0288.pythonanywhere.com/static/users/{chat_id}/{datetime.datetime.now().isocalendar()[0]}_{datetime.datetime.now().isocalendar()[1]}/fasts/progress_{datetime.datetime.now().strftime('%y-%m-%d')}.png"
                message = "Hey 🙂. Hier siehst du, wie lange du letzte Woche gefastet hast. Wie denkst du über deine Woche? Was blieb dir besonders in Erinnerung? ✏"
                # create message_elements
                message_elements = {'update_id': None, 'created_at': None, 'received_at': None, 'message_id': None, 'message': message, 'intent': '/progress', 'keyboard': None, 'user_id': None, 'first_name': None, 'chat_id': chat_id, 'chat_title': None, 'chat_type': None, 'bot_command': None, 'key_value': 'past_week_text', 'callback_url': None, 'img': img, 'is_bot': None, 'language_code': None, 'callback_query_id': None, 'group_chat_created': None, 'new_chat_participant_id': None}

                # send msg
                Bot.send_trigger_photo(message_elements)        
            
            except Exception as e:
                print(e)
