#!/usr/bin/python3.6
# coding: utf8
import logging
import numpy as np
import pandas as pd
import datetime
import json
import os

from db_bot import DBBot
from fast_overview import get_output_location, get_fasting_data, create_overview

import sys #required because files in parent folder
sys.path.append('../')
import config

DBBot = DBBot()

class DialogueBot:
    def setup(self):
        # wipe existing dialogues first
        DBBot.wipe_dialogues()
        print('wiped dialogues')
        # load the dialogues into the db
        file_identifiers = os.listdir("{}/dialogues/".format(config.DIRECTORY))
        # remove hidden files
        file_identifiers = [i for i in file_identifiers if i.endswith('.csv')]
        # remove extension
        file_identifiers = [os.path.splitext(each)[0] for each in file_identifiers]
        DialogueBot.save_dialogues(file_identifiers)

    def save_dialogues(file_identifiers):
        print('saving dialogues')
        for identifier in file_identifiers:
            data = pd.read_csv("{}/dialogues/{}.csv".format(config.DIRECTORY, identifier), dtype= str, delimiter=',')
            # translate NaN cells into None cells
            data = data.where(pd.notnull(data), None)
            # transform keyboard, callback, url lists into actual lists
            f = lambda x: x.split("; ") if x is not None else x
            data["keyboard"] = data["keyboard"].apply(f)
            data["callback_url"] = data["callback_url"].apply(f)
            # transform array into subscriptable numpy array
            data=np.array(data, dtype=object)
            #add slash to match the intent
            identifier = '/' + identifier
            DBBot.add_dialogue(identifier, json.dumps(data.tolist()))

    def fetch_dialogue(file_identifier):
        data = DBBot.get_dialogue(file_identifier)
        data = json.loads(data[0][2])
        data = np.array(data, dtype = object)
        # convert strings into list
        return data

    def fetch_last_messages(data, chat_id, last_user_message=None, last_bot_message=None):
        # if triggered, the last_user_message will be set to "✏"
        if last_user_message is None:
            # get last user message
            last_user_message = DBBot.get_last_message(chat_id, 0)[1]
        # check if user provided open answer - if so, change message to "✏". If user sent photo, start meal_entry
        if len(data[data[:, 1]==last_user_message, 0]) == 0:
            if np.char.startswith(data[:, 1][0], config.user_photo) and "photo" in last_user_message:
                last_user_message = data[:, 1][0]
            else:
                last_user_message = "✏"

        # if triggered, the last_bot_message will be set to "✏"
        if last_bot_message is None:
            # get last bot message; if there is no previous bot message, set "✏"
            result_last_bot_message = DBBot.get_last_message(chat_id, 1)
            if result_last_bot_message == None:
                last_bot_message = "✏"
            else:
                last_bot_message = result_last_bot_message[1]

        # check if bot response is in array; if not, change message to "✏"
        last_bot_message_for_exception = None
        if len(data[data[:, 0]==last_bot_message, 0]) == 0:
            # this value is used for the except: statement
            last_bot_message_for_exception = last_bot_message
            last_bot_message = "✏"
        return last_user_message, last_bot_message, last_bot_message_for_exception

    def extract_response_array(response_array, chat_id, fast_duration):
        ## even though fast_duration is not explicitly mentioned in this function, it is used within the "if '{}' in message:" section.

        # save parameters
        message = response_array[2]
        keyboard = response_array[3]
        callback_url = response_array[4]
        img = response_array[5]
        key_value = response_array[6]
        intent = response_array[7]
        # check for db values in msg (chat_id, datetime)
        if '{}' in message:
            # convert string to message with .format
            message = eval(message)
        # check for db values in img
        if img and '{}' in img:
            img = eval(img)
        return message, keyboard, callback_url, img, key_value, intent

    def get_fast_values(chat_id):
        # get datetime of start of fast
        try:
            data = DBBot.get_fast_values(chat_id, 'fast_start_text')
            fast_start = data[0][0]
        except:
            fast_start = datetime.datetime.now()
        # set fast_end to now() and calculate difference between fast_end and fast_start
        fast_end = datetime.datetime.now()
        difference = fast_end - fast_start
        seconds_in_day = 24 * 60 * 60
        fast_duration_hours = divmod(difference.days * seconds_in_day + difference.seconds, 3600)[0]
        fast_duration_mins = divmod(difference.days * seconds_in_day + difference.seconds, 60)[0] - fast_duration_hours*60
        fast_duration = f"{fast_duration_hours} Stunden und {fast_duration_mins} Minuten"

        return fast_duration

    def handle_open_conversation(intent, chat_id):
        message, keyboard, callback_url, img, key_value, intent = DialogueBot.handle_key_value_conversation("/befehle", chat_id, last_user_message="/befehle", last_bot_message="✏")
        return message, keyboard, callback_url, img, key_value, intent


    def handle_key_value_conversation(intent, chat_id, last_user_message=None, last_bot_message=None, fast_duration=None):
        # get the dialogue
        try:
            data = DialogueBot.fetch_dialogue(intent)
        except Exception as e:
            logging.exception("Could not find intent in get_response")
            intent = '/befehle'
            last_user_message = '/befehle'
            data = DialogueBot.fetch_dialogue(intent)
        
        ## for fasting intents: 
        # fasten_start: create fasting plot
        if intent == '/fasten':
            output_file_location = get_output_location(chat_id)
            df_fast = get_fasting_data(chat_id)
            create_overview(df_fast, output_file_location)
        # fasten_end: get fasting values
        elif intent == '/fasten_end':
            fast_duration = DialogueBot.get_fast_values(chat_id)

        last_user_message, last_bot_message, last_bot_message_for_exception = DialogueBot.fetch_last_messages(data, chat_id, last_user_message, last_bot_message)
        try:
            response_array = data[(intent == last_user_message == data[:,1]) | ((last_bot_message == data[:,0]) & (last_user_message == data[:,1]))][0]
        except:
            # check if {} formating values have been used - necessary for processing the user message
            temp = data[np.array(["{}" in s for s in data[:,0]])]
            for num, row in enumerate(temp):
                if last_user_message == temp[num, 1] and last_bot_message_for_exception == eval(temp[num, 0]):
                    response_array = temp[num, :]
        # check if response_array exists. If not, set default answer <- catch-all for errors in dialogues
        if 'response_array' not in locals():
            try:
                print(f'intent: {intent}')
                print(f'last_bot_message: {last_bot_message}')
                print(f'data[:,1]: {data[:,1]}')
                print(f'data[:,0]: {data[:,0]}')
                # check if the user double clicked a button by replacing the user message with "✏".
                response_array = data[(intent == "✏" == data[:,1]) | ((last_bot_message == data[:,0]) & ("✏" == data[:,1]))][0]
            except Exception as e:
                logging.exception("No matching answer")
                response_array = ['✏', '✏', 'Tut mir leid. Das verstehe ich nicht 😔. Ich habe meine Macher schon verständigt.', None, None, None, None, None, '/open_conversation']

        message, keyboard, callback_url, img, key_value, intent = DialogueBot.extract_response_array(response_array, chat_id, fast_duration)

        return message, keyboard, callback_url, img, key_value, intent


    # improve function by creating an object that holds additional user info (e.g. fast values)
    def get_response(self, intent, chat_id):
        ## route according to intent
        # open conversation
        if intent in ['open_conversation', 'end_conversation']:
            message, keyboard, callback_url, img, key_value, intent = DialogueBot.handle_open_conversation(intent, chat_id)
            logging.info(f'Open dialogue by {chat_id}')
        # key_value conversation
        else:
            message, keyboard, callback_url, img, key_value, intent = DialogueBot.handle_key_value_conversation(intent, chat_id)
        
        return message, keyboard, callback_url, img, key_value, intent


