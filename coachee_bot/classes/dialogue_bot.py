#!/usr/bin/python3.6
# coding: utf8
import numpy as np
import pandas as pd
import datetime
import json
import os

import sys #required because files in parent folder
sys.path.append('../')
import config

import sys #required because files in other folder
sys.path.append('../classes/')
from dbhelper import DBHelper
from data_bot import DataBot

db = DBHelper()
DataBot = DataBot()

class DialogueBot:
    def setup(self):
        # wipe existing dialogues first
        db.wipe_dialogues()
        print('wiped dialogues')
        # load the dialogues into the db
        file_identifiers = os.listdir("{}/dialogues/".format(config.DIRECTORY))
        # remove hidden files
        file_identifiers = [i for i in file_identifiers if i.endswith('.csv')]
        # remove extension
        file_identifiers = [os.path.splitext(each)[0] for each in file_identifiers]
        DialogueBot.save_dialogues(file_identifiers)

    def save_dialogues(file_identifiers):
        for identifier in file_identifiers:
            data = pd.read_csv("{}/dialogues/{}.csv".format(config.DIRECTORY, identifier), dtype= str, delimiter=',')
            # translate NaN cells into None cells
            data = data.where(pd.notnull(data), None)
            # transform keyboard list into actual list
            f = lambda x: x.split("; ") if x is not None else x
            data["keyboard"] = data["keyboard"].apply(f)
            # transform array into subscriptable numpy array
            data=np.array(data, dtype=object)
            #add slash to match the intent
            identifier = '/' + identifier
            db.add_dialogue(identifier, json.dumps(data.tolist()))

    def fetch_dialogue(file_identifier):
        data = db.get_dialogue(file_identifier)
        data = json.loads(data[0][2])
        data = np.array(data, dtype = object)
        # convert strings into list
        return data

    def fetch_last_messages(data, chat_id, last_user_message=None, last_bot_message=None):
        # if triggered, the last_user_message will be set to "✏"
        if last_user_message is None:
            # get last user message
            last_user_message = db.get_last_message(chat_id, 0)[1]
        # if triggered, the last_bot_message will be set to "✏"
        if last_bot_message is None:
            # get last bot message; if there is no previous bot message, set "✏"
            result_last_bot_message = db.get_last_message(chat_id, 1)
            if result_last_bot_message == None:
                last_bot_message = "✏"
            else:
                last_bot_message = result_last_bot_message[1]
        # check if user provided open answer; if so, change message to "✏"

        if len(data[data[:, 1]==last_user_message, 0]) == 0:
            if np.char.startswith(data[:, 1][0], "/meal_entry"):
                last_user_message = data[:, 1]
            else:
                last_user_message = "✏"
        # check if bot response is in array; if not, change message to "✏"
        last_bot_message_for_exception = None
        if len(data[data[:, 0]==last_bot_message, 0]) == 0:
            # this value is used for the except: statement
            last_bot_message_for_exception = last_bot_message
            last_bot_message = "✏"
        return last_user_message, last_bot_message, last_bot_message_for_exception

    def extract_response_array(response_array, chat_id, first_name=None, ci_plan=None, my_week=None, motivation=None):
        # save parameters
        message = response_array[2]
        # check for key_values (first_name, ci_plan, motivation, my_week, ...)
        if '{}' in message:
            # convert string to message with .format
            message = eval(message)

        keyboard = response_array[3]
        # convert str to boolean
        resize_keyboard = response_array[4]
        if resize_keyboard:
            resize_keyboard = False
        else:
            resize_keyboard = True
        inline_keyboard = response_array[5]
        if inline_keyboard:
            inline_keyboard = json.loads(response_array[5])
        photo = response_array[6]
        if photo:
            if '{}' in photo:
                photo = eval(photo)
        key_value = response_array[7]

        intent = response_array[8]

        return message, keyboard, resize_keyboard, inline_keyboard, photo, key_value, intent

    def check_and_find_component(chat_id):
        # find user progress so far and create numpy array for indexing
        progress = []
        progress_data = db.get_user_progress(chat_id)
        for num, row in enumerate(progress_data):
            progress.append(progress_data[num][4])
        progress = np.array(progress, dtype=object)

        # load order of components
        component_data = pd.read_csv("{}/dialogues/components/components.csv".format(config.DIRECTORY), dtype= str, delimiter=',')
        components = component_data.sort_values(by=['priority'])['title']
        # necessary to reset the indices for proper indexing
        components = components.reset_index(drop=True)

        # check if a user has not received a specific component yet
        component = []
        for num, row in enumerate(components):
            # add component, if the user has either made no progress so far (len(progress) == 0) or the component is missing
            if len(progress) == 0 or sum(components[num] == progress) == 0:
                component = components[num]
                created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if db.check_user_progress(chat_id, component) == 0:
                    try:
                        db.add_user_progress(telegram_id=chat_id, chat_id=chat_id, category='content', component=component, started_at=created_at, completed_at=None, created_at=created_at)
                    except Exception as e:
                        # add error to error table - better would be queue
                        context = 'add_user_progress'
                        db.add_error(created_at, chat_id, context, str(e))
                return component
        return component

    def complete_component(chat_id, component):
        completed_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            db.update_user_progress(completed_at, chat_id, component)
        except Exception as e:
            # add error to error table - better would be queue
            created_at = completed_at
            context = 'update_user_progress'
            db.add_error(created_at, chat_id, context, str(e))

    def check_and_find_vrp(chat_id):
        # find user progress so far and create numpy array for indexing
        progress = []
        progress_data = db.get_user_progress(chat_id)
        for num, row in enumerate(progress_data):
            progress.append(progress_data[num][4])
        progress = np.array(progress)
        # load order of vrps
        data = pd.read_csv("{}/dialogues/components/vrps.csv".format(config.DIRECTORY), dtype= str, delimiter=',')
        vrps = data.sort_values(by=['priority'])['title']
        # necessary to reset the indices for proper indexing
        vrps = vrps.reset_index(drop=True)
        # check if a user has not received a specific component yet
        vrp = []
        for num, row in enumerate(vrps):
            # add component, if the user has either made no progress so far (len(progress) == 0) or the component is missing
            if len(progress) == 0 or sum(vrps[num] == progress) == 0:
                vrp = vrps[num]
                created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if db.check_user_progress(chat_id, vrp) == 0:
                    try:
                        db.add_user_progress(telegram_id=chat_id, chat_id=chat_id, category='content', component=vrp, started_at=created_at, completed_at=created_at, created_at=created_at)
                    except Exception as e:
                        # add error to error table - better would be queue
                        context = 'add_user_progress'
                        db.add_error(created_at, chat_id, context, str(e))
                return vrp
        return vrp

    def start_challenge(chat_id, intent):
        created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        challenge_index = pd.read_csv("{}/dialogues/components/challenges.csv".format(config.DIRECTORY), dtype= str, delimiter=',')
        challenge_index = np.array(challenge_index, dtype=object)
        try:
            challenge = challenge_index[(challenge_index[:, 0] == intent), 1][0]
        # if no challenge defined for dialogue
        except:
            challenge = intent

        try:
            db.add_user_progress(telegram_id=chat_id, chat_id=chat_id, category='challenge', component=challenge, started_at=created_at, completed_at=None, created_at=created_at)
        except Exception as e:
            # add error to error table - better would be queue
            created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            context = 'start_challenge'
            db.add_error(created_at, chat_id, context, str(e))

    def get_plan(chat_id, intent):
        if intent in ['/check_in', '/wiegen']:
            plan_data = db.get_key_values('ci_plan', chat_id, limit=7)
            # only keep yesterday's plan
            yesterday = datetime.datetime.now().date() - datetime.timedelta(days=1)
            plan = []
            for num in range(0,len(plan_data)):
                created_at_day = plan_data[num][5].date()
                if created_at_day == yesterday:
                    plan = plan_data[num][4]
                    break

            if intent == '/check_in':
                if plan == [] or plan == 'Nein, will mir nichts vornehmen' or plan == 'Nicht jetzt' or plan == 'Hast du ein Beispiel?' or plan == 'Ja' or plan == 'Alles klar. Ich weiß etwas':
                    plan = "Du hast dir gestern nichts für heute vorgenommen. Mach am Ende des Dialogs einen Plan und wir besprechen ihn an dieser Stelle morgen Abend. Schreib jetzt einfach 'Ok'. ✏"
                else:
                    plan = 'Das hast du dir gestern für heute vorgenommen:\n\n' + plan + '\n\nWie erging es dir damit? ✏'
            elif intent == '/wiegen' and (chat_id == 669362429):
                plan = 'Super Arbeit. Hier siehst du, zu welchen Zeiten dein Körper gestern zu arbeiten hatte: http://s0288.pythonanywhere.com/static/food/cs_{}.png \n\nHab einen schönen Tag heute ☺'.format((datetime.date.today() - datetime.timedelta(1)).strftime("%y-%m-%d"))
            elif intent == '/wiegen' and (chat_id == 530046467):
                plan = 'Super Arbeit. Hier siehst du, zu welchen Zeiten dein Körper gestern zu arbeiten hatte: http://s0288.pythonanywhere.com/static/food/dm_{}.png \n\nHab einen schönen Tag heute ☺'.format((datetime.date.today() - datetime.timedelta(1)).strftime("%y-%m-%d"))
            elif intent == '/wiegen' and (chat_id == 431486544):
                plan = 'Super Arbeit. Hier siehst du, zu welchen Zeiten dein Körper gestern zu arbeiten hatte: http://s0288.pythonanywhere.com/static/food/db_{}.png \n\nHab einen schönen Tag heute ☺'.format((datetime.date.today() - datetime.timedelta(1)).strftime("%y-%m-%d"))
            elif intent == '/wiegen' and (chat_id == 533981237):
                plan = 'Super Arbeit. Hier siehst du, zu welchen Zeiten dein Körper gestern zu arbeiten hatte: http://s0288.pythonanywhere.com/static/food/aj_{}.png \n\nHab einen schönen Tag heute ☺'.format((datetime.date.today() - datetime.timedelta(1)).strftime("%y-%m-%d"))
            elif intent == '/wiegen' and (chat_id == 495346285):
                plan = 'Super Arbeit. Hier siehst du, zu welchen Zeiten dein Körper gestern zu arbeiten hatte: http://s0288.pythonanywhere.com/static/food/ag_{}.png \n\nHab einen schönen Tag heute ☺'.format((datetime.date.today() - datetime.timedelta(1)).strftime("%y-%m-%d"))
            elif intent == '/wiegen' and (chat_id == 636513187 or chat_id == 415604082):
                plan = 'Super Arbeit. Hier siehst du, zu welchen Zeiten dein Körper gestern zu arbeiten hatte: http://s0288.pythonanywhere.com/static/food/ek_{}.png \n\nHab einen schönen Tag heute ☺'.format((datetime.date.today() - datetime.timedelta(1)).strftime("%y-%m-%d"))
            elif intent == '/wiegen' and (chat_id == 646768332):
                plan = 'Super Arbeit. Hier siehst du, zu welchen Zeiten dein Körper gestern zu arbeiten hatte: http://s0288.pythonanywhere.com/static/food/mb_{}.png \n\nHab einen schönen Tag heute ☺'.format((datetime.date.today() - datetime.timedelta(1)).strftime("%y-%m-%d"))

            else:
                if plan == [] or plan == 'Nein, will mir nichts vornehmen' or plan == 'Nicht jetzt' or plan == 'Hast du ein Beispiel?' or plan == 'Ja':
                    plan = "Genieße deinen Tag heute!"
                else:
                    plan = 'Genieße deinen Tag!\n\nDas hast du dir für heute vorgenommen: ' + plan + '\n\nViel Erfolg dabei ☺'

        elif intent in ['/5_steps']:
            # get motivtion of user
            plan_data = db.get_key_values('motivation', chat_id, limit=1)[0][4]
            print(plan_data)
            plan = []
            plan = "Hey ☺. Deshalb willst du dein Ziel erreichen: {}. \n\nMöchtest du etwas notieren, das dich von diesem Ziel entfernt hat und das du in Zukunft anders machen möchtest?".format(plan_data)
        return plan

    def get_week(chat_id):
        try:
            # extract needed data
            mood_data = db.get_key_values('ci_mood', chat_id, limit=6)
            proudMoment = db.get_key_values('ci_proudMoments', chat_id, limit=6)
            makeBetter = db.get_key_values('ci_makeBetter', chat_id, limit=6)
            ci_plan = db.get_key_values('ci_plan', chat_id, limit=6)

            # prep my week info
            mood_day = []
            created_at_day = []
            pM_day = []
            mB_day = []
            plan_day = []
            message = "Und hier siehst du deine Woche im Überblick: "
            n = len(mood_data)
            for num in range(0,n):
                i =  n - num - 1
                mood_day = DataBot.convert_to_emoji(int(mood_data[i][4]))
                created_at_day = mood_data[i][5].date()
                dow = DataBot.convert_to_dow(created_at_day.weekday())
                try:
                    pM_day = proudMoment[i][4]
                    mB_day = makeBetter[i][4]
                    plan_day = ci_plan[i][4]
                except Exception as e:
                    print(e)
                message = message + "\n\n{}, {}: \n{} \nWar gut: {} \nWar nicht gut: {} \nIn Zukunft: {}".format(dow, created_at_day, mood_day, pM_day, mB_day, plan_day)
            message = message + "\n\nHat dich dein Verhalten deinem Ziel näher gebracht?"
            return message
        except Exception as e:
            print(e)

    def get_motivation(chat_id):
        try:
            motivation = db.get_key_values('motivation', chat_id, limit=1)[0][4]
            target_value = db.get_key_values('target_value', chat_id, limit=1)

            if len(motivation) > 0 and len(target_value) == 0:
                motivation = "Darum möchtest du abnehmen: {}. Hat dich dein Verhalten der letzten 24 Stunden deinem Ziel näher gebracht?".format(motivation)
            elif len(motivation) > 0 and len(target_value) > 0:
                motivation = "Darum möchtest du abnehmen: {}. Und das ist dein konkretes Ziel: {} Kilo. Hat dich dein Verhalten der letzten 24 Stunden deinem Ziel näher gebracht?".format(motivation, target_value[0][4])
            return motivation
        except Exception as e:
            print(e)

    def find_response(self, intent, chat_id, first_name=None, ci_plan=None, my_week=None, motivation=None, last_user_message=None, last_bot_message=None):
        # get the dialogue
        print(intent)
        try:
            data = DialogueBot.fetch_dialogue(intent)
        except Exception as e:
            # add error to error table - better would be queue
            created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            context = 'dialogue_find_response'
            db.add_error(created_at, chat_id, context, str(e))

            intent = '/wrong_command'
            last_user_message = '/wrong_command'
            data = DialogueBot.fetch_dialogue(intent)

        last_user_message, last_bot_message, last_bot_message_for_exception = DialogueBot.fetch_last_messages(data, chat_id, last_user_message, last_bot_message)
        print(last_user_message)
        print(last_bot_message)
        # find the answer
        try:
            # find the value pair of last_user_message and last_bot_message that provides the right answer - if the user message includes '/check_in', ignore the last bot response
            response_array = data[(intent == last_user_message == data[:,1]) | ((last_bot_message == data[:,0]) & (last_user_message == data[:,1]))][0]
        except:
            # check if {} formating values have been used - necessary for processing the user message
            temp = data[np.array(["{}" in s for s in data[:,0]])]
            for num, row in enumerate(temp):
                if "ci_plan" in temp[num, 0]:
                    ci_plan = DialogueBot.get_plan(chat_id, intent)
                elif "my_week" in temp[num, 0]:
                    my_week = DialogueBot.get_week(chat_id)
                elif "motivation" in temp[num, 0] and intent in ['/start', '/check_in']:
                    motivation = DialogueBot.get_motivation(chat_id)
                print('in exception')
                if last_user_message == temp[num, 1] and last_bot_message_for_exception == eval(temp[num, 0]):
                    response_array = temp[num, :]
        # check if response_array exists. If not, set default answer <- catch-all for errors in dialogues
        if 'response_array' not in locals():
            try:
                # check if the user double clicked a button by replacing the user message with "✏".
                response_array = data[(intent == "✏" == data[:,1]) | ((last_bot_message == data[:,0]) & ("✏" == data[:,1]))][0]
            except:
                # add error to error table - better would be queue
                created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                context = 'dialogue_no_response_array'
                db.add_error(created_at, chat_id, context, intent)
                response_array = ['✏', '✏', 'Tut mir leid. Das verstehe ich nicht 😔. Ich habe meine Macher schon verständigt.', None, None, None, None, None, '/open_conversation']

        # necessary for the bot message
        if "ci_plan" in response_array[2]:
            ci_plan = DialogueBot.get_plan(chat_id, intent)
        elif "my_week" in response_array[2]:
            my_week = DialogueBot.get_week(chat_id)
        elif "motivation" in response_array[2] and intent in ['/start', '/check_in']:
            motivation = DialogueBot.get_motivation(chat_id)
        message, keyboard, resize_keyboard, inline_keyboard, photo, key_value, intent = DialogueBot.extract_response_array(response_array, chat_id, first_name, ci_plan, my_week, motivation)
        ## check if open components at end of check_in
        if key_value == 'component':
            print('looking for component')
            component_intent = DialogueBot.check_and_find_component(chat_id)
            if len(component_intent) > 0:
                message, keyboard, resize_keyboard, inline_keyboard, photo, key_value, intent = DialogueBot.find_response(self, component_intent, chat_id, first_name=first_name, last_user_message=component_intent, last_bot_message="✏")
        elif key_value == 'vrp':
            print('looking for vrp')
            vrp = DialogueBot.check_and_find_vrp(chat_id)
            if len(vrp) > 0:
                message, keyboard, resize_keyboard, inline_keyboard, photo, key_value, intent = DialogueBot.find_response(self, vrp, chat_id, first_name=first_name, last_user_message=vrp, last_bot_message="✏")
        elif key_value == 'c_completed':
            print('updating user_progress')
            DialogueBot.complete_component(chat_id, intent)
        elif key_value == 'challenge_start':
            print('starting challenge')
            DialogueBot.start_challenge(chat_id, intent)

        return message, keyboard, resize_keyboard, inline_keyboard, photo, key_value, intent
