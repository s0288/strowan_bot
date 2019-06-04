#!/usr/bin/python3.6
# coding: utf8
import requests
import json
import datetime
import pytz
local_tz = pytz.timezone('Europe/Berlin')
import urllib
import time

import numpy as np
import pandas as pd
import os

import random

import sys #required because files in parent folder
sys.path.append('../')
import config

import sys #required because files in other folder
sys.path.append('../classes/')
from dbhelper import DBHelper
from dialogue_bot import DialogueBot
from data_bot import DataBot

TOKEN = config.TELEGRAM_TOKEN
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
db = DBHelper()
DialogueBot = DialogueBot()
DataBot = DataBot()

class Bot:
    ## ------ support functions
    # ------ process incoming messages
    def get_url(url):
        response = requests.get(url)
        content = response.content.decode("utf8")
        return content

    def get_json_from_url(url):
        content = Bot.get_url(url)
        js = json.loads(content)
        return js

    def get_updates(self, offset=None):
        url = URL + "getUpdates?timeout=600"
        if offset:
            url += "&offset={}".format(offset)
        js = Bot.get_json_from_url(url)
        return js

    def get_last_update_id(self, updates):
        update_ids = []
        for update in updates["result"]:
            update_ids.append(int(update["update_id"]))
        return min(update_ids)

    def answer_callback(callback_query_id, text=None):
        url = URL + "answerCallbackQuery?callback_query_id={}".format(callback_query_id)
        if text:
            url += "&text={}".format(text)
        Bot.get_url(url)
    # ------ end: process incoming messages

    # ------ extract content of incoming messages
    def check_content(update):
        content = None
        # check whether we're dealing with a message or a callback
        if update.get('message') is not None:
            # check whether we're dealing with a text message or other message types (file, sticker, picture, audio, etc.)
            if update["message"].get('text') is not None:
                content = 'text'
            elif update["message"].get('sticker') is not None:
                print('user_sent_sticker')
                content = 'sticker'
            elif update["message"].get('photo') is not None:
                content = 'photo'
            elif update["message"].get('document') is not None:
                content = 'document'
            elif update["message"].get('group_chat_created') is not None:
                print('group_chat_created')
                content = 'group_chat_created'
            elif update["message"].get('new_chat_participant') is not None:
                print('new_chat_participant')
                content = 'new_chat_participant'
            elif update["message"].get('left_chat_participant') is not None:
                print('left_chat_participant')
                content = 'left_chat_participant'
        elif update.get('callback_query') is not None:
            content = 'callback'
        return content

    def extract_message(update):
        # update_elements(update_id, created_at, message_id, message, user_id, first_name, chat_id, chat_type, is_bot, language_code, callback_query_id, group_chat_created, new_chat_participant_id)
        update_elements = {'update_id': None, 'created_at': None, 'message_id': None, 'message': None, 'intent': None, 'keyboard': None, 'user_id': None, 'first_name': None, 'chat_id': None, 'chat_title': None, 'chat_type': None, 'bot_command': None, 'key_value': None, 'is_bot': None, 'language_code': None, 'callback_query_id': None, 'group_chat_created': None, 'new_chat_participant_id': None}
        # save attributes
        update_elements['update_id'] = update["update_id"]
        created_at = datetime.datetime.fromtimestamp(int(update["message"]["date"]))
        update_elements['created_at'] = created_at.strftime('%Y-%m-%d %H:%M:%S')
        #update_elements['created_at'] = created_at.replace(tzinfo=pytz.utc).astimezone(local_tz).strftime('%Y-%m-%d %H:%M:%S')
        update_elements['message_id'] = update["message"]["message_id"]
        # if the message has text, save it
        if update["message"].get('text') is not None:
            update_elements['message'] = update["message"]["text"]
        elif update["message"].get('document') is not None:
            update_elements['message'] = update["message"]["document"]["file_name"]
        elif update["message"].get('photo') is not None:
            try:
                update_elements['message'] = 'photo: ' + update["message"]["photo"][3]["file_id"]
                update_elements['key_value'] = 'user_photo'
            except:
                update_elements['message'] = 'photo: ' + update["message"]["photo"][0]["file_id"]
                update_elements['key_value'] = 'user_photo'
        update_elements['user_id'] = update["message"]["from"]["id"]
        update_elements['first_name'] = update["message"]["from"]["first_name"]
        update_elements['chat_id'] = update["message"]["chat"]["id"]
        # if the chat has a title, save it
        if update["message"]["chat"].get('title') is not None:
            update_elements['chat_title'] = update["message"]["chat"]["title"]
        update_elements['chat_type'] = update["message"]["chat"]["type"]
        # if the user sends a bot_command (e.g. /start or /check_in), save it
        if update["message"].get('entities') is not None:
            for entity in update["message"]["entities"]:
                update_elements['bot_command'] = entity["type"]
        update_elements['is_bot'] = update["message"]["from"]["is_bot"]
        # if the message has a language code, save it
        if update["message"]["from"].get('language_code') is not None:
            update_elements['language_code'] = update["message"]["from"]["language_code"]
        # if a new group created, save it
        if update["message"].get('group_chat_created') is not None:
            update_elements['group_chat_created'] = update["message"]["group_chat_created"]
        # if a new participant is added, save it
        if update["message"].get('new_chat_participant') is not None:
            update_elements['new_chat_participant_id'] = update["message"]["new_chat_participant"]["id"]
        # if a sticker is provided, save it
        if update["message"].get('sticker') is not None:
            update_elements['message'] = update["message"]["sticker"]["emoji"]
        return update_elements

    def extract_callback(update):
        # update_elements(update_id, created_at, message_id, message, user_id, first_name, chat_id, chat_type, is_bot, language_code, callback_query_id)
        update_elements = {'update_id': None, 'created_at': None, 'message_id': None, 'message': None, 'intent': None, 'keyboard': None, 'user_id': None, 'first_name': None, 'chat_id': None, 'chat_title': None, 'chat_type': None, 'bot_command': None, 'key_value': None, 'is_bot': None, 'language_code': None, 'callback_query_id': None, 'group_chat_created': None, 'new_chat_participant_id': None}
        # save callback_query_id
        callback_query_id = update["callback_query"]["id"]
        # remove loading button on the client
        Bot.answer_callback(callback_query_id)
        # save remaining parameters
        update_elements['update_id'] = update["update_id"]
        created_at = datetime.datetime.fromtimestamp(int(update["callback_query"]["message"]["date"]))
        update_elements['created_at'] = created_at.strftime('%Y-%m-%d %H:%M:%S')
        #update_elements['created_at'] = created_at.replace(tzinfo=pytz.utc).astimezone(local_tz).strftime('%Y-%m-%d %H:%M:%S')
        update_elements['message_id'] = update["callback_query"]["message"]["message_id"]
        update_elements['message'] = update["callback_query"]["data"]
        update_elements['user_id'] = update["callback_query"]["from"]["id"]
        update_elements['first_name'] = update["callback_query"]["from"]["first_name"]
        update_elements['chat_id'] = update["callback_query"]["message"]["chat"]["id"]
        # if the chat has a title, save it
        if update["callback_query"]["message"]["chat"].get('title') is not None:
            update_elements['chat_title'] = update["callback_query"]["message"]["chat"]["title"]
        update_elements['chat_type'] = update["callback_query"]["message"]["chat"]["type"]
        update_elements['is_bot'] = update["callback_query"]["from"]["is_bot"]
        # if the message has a language code, save it
        if update["callback_query"]["from"].get('language_code') is not None:
            update_elements['language_code'] = update["callback_query"]["from"]["language_code"]
        update_elements['callback_query_id'] = callback_query_id
        return update_elements

    def answer_callback(callback_query_id, text=None):
        url = URL + "answerCallbackQuery?callback_query_id={}".format(callback_query_id)
        if text:
            url += "&text={}".format(text)
        Bot.get_url(url)

    def get_intent(update_elements):
        # set action for bot_commands and externally triggered messages
        if update_elements["bot_command"] == 'bot_command':
            update_elements["intent"] = update_elements["message"].lower()
        # if there is no bot command, continue the discussion that is under way or set 'open_conversation'
        else:
            # get the intent and the key value of the last message
            last_bot_message = db.get_last_message(update_elements["chat_id"], 1)
            # it is possible that there are no bot messages yet, therefore check if None
            if last_bot_message:
                last_intent, last_msg, last_key_value = last_bot_message[0], last_bot_message[1], last_bot_message[2]
                if update_elements['key_value'] in ('user_photo', 'meal_entry'):
                    update_elements["intent"] = '/meal_entry'
                elif last_intent == 'end_conversation' or last_intent is None:
                    update_elements["intent"] = 'open_conversation'
                else:
                    update_elements["intent"] = last_intent
                    if update_elements["key_value"] != 'user_photo':
                        update_elements["key_value"] = last_key_value
            else:
                update_elements["intent"] = 'open_conversation'
        return update_elements

    def save_updates(update_elements, start_time=None):
        # add update_id, created_at, message_id, message, user_id, chat_id, chat_type, bot_command, callback_query_id, is_bot
        print('is_bot: ' + str(update_elements['is_bot']) + ', message: ' + str(update_elements['message']))

        # check if user is in db already; if not, add him
        ## for this we can define a global variable later to avoid checking the db at every message
        if update_elements['is_bot'] is not None:
            if db.check_user(update_elements['user_id']) == 0:
                # add user_id, first_name, created_at, is_bot, language_code
                db.add_user(update_elements['user_id'], update_elements['first_name'], update_elements['created_at'], update_elements['is_bot'], update_elements['language_code'])
            # set to 1 for bot answer to make sure everything works without an update even
        else:
            update_elements['is_bot'] = True

        if update_elements['created_at'] is None:
            # set current date and time - updated with update statement
            update_elements['created_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        try:
            if start_time is None:
                db.add_update(update_elements['message_id'], update_elements['created_at'], update_elements['message'], update_elements['intent'], update_elements['user_id'], update_elements['chat_id'], update_elements['chat_type'], update_elements['bot_command'], update_elements['key_value'], update_elements['is_bot'], update_elements['callback_query_id'], update_elements['group_chat_created'], update_elements['new_chat_participant_id'], update_elements['update_id'])
            else:
                time_to_start = time.time() - start_time
                db.add_update(update_elements['message_id'], update_elements['created_at'], update_elements['message'], update_elements['intent'], update_elements['user_id'], update_elements['chat_id'], update_elements['chat_type'], update_elements['bot_command'], update_elements['key_value'], update_elements['is_bot'], update_elements['callback_query_id'], update_elements['group_chat_created'], update_elements['new_chat_participant_id'], update_elements['update_id'], time_to_start)
        except Exception as e:
            # add error to error table - better would be queue
            created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            context = 'save_updates'
            chat_id = update_elements['chat_id']
            db.add_error(created_at, chat_id, context, str(e))
        # return for update statement
        return update_elements['created_at']

    def update_updates(update_elements, created_at_self):
        # find and update row
        try:
            db.update_update(created_at_self, update_elements['message_id'], update_elements['created_at'], update_elements['message'], update_elements['intent'], update_elements['user_id'], update_elements['chat_id'], update_elements['chat_type'], update_elements['bot_command'], update_elements['key_value'], update_elements['is_bot'], update_elements['callback_query_id'], update_elements['group_chat_created'], update_elements['new_chat_participant_id'], update_elements['update_id'])
        except Exception as e:
            # add error to error table - better would be queue
            created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            context = 'update_updates'
            chat_id = update_elements['chat_id']
            db.add_error(created_at, chat_id, context, str(e))

    # main extract_ function that defines where an update is routed towards
    def extract_updates(self, updates, start_time=None):
        for update in updates["result"]:
            # check whether we're dealing with a message or a callback
            content = Bot.check_content(update)

            if content == 'text' or content == 'group_chat_created' or content == 'new_chat_participant':
                update_elements = Bot.extract_message(update)
            elif content == 'sticker':
                update_elements = Bot.extract_message(update)
            elif content == 'photo':
                update_elements = Bot.extract_message(update)
            elif content == 'document':
                update_elements = Bot.extract_message(update)
            elif content == 'callback':
                update_elements = Bot.extract_callback(update)

            if content not in ['left_chat_participant', 'new_chat_participant', 'group_chat_created']:
                update_elements = Bot.get_intent(update_elements)
                Bot.save_updates(update_elements, start_time)
                return update_elements
    # ------ end: extract content of incoming messages
    # ------ extract content of outgoing messages
    def extract_load(send_elements, url_response):
        # save parameters
        created_at = datetime.datetime.fromtimestamp(int(url_response['result']["date"]))
        send_elements['created_at'] = created_at.strftime('%Y-%m-%d %H:%M:%S')
        #send_elements['created_at'] = created_at.replace(tzinfo=pytz.utc).astimezone(local_tz).strftime('%Y-%m-%d %H:%M:%S')
        send_elements['message_id'] = url_response['result']["message_id"]
        send_elements['user_id'] = url_response['result']["from"]["id"]
        send_elements['first_name'] = url_response['result']["from"]["first_name"]
        send_elements['chat_id'] = url_response['result']["chat"]["id"]
        # if the chat has a title, save it
        if url_response['result']["chat"].get('title') is not None:
            send_elements['chat_title'] = url_response['result']["chat"]["title"]
        send_elements['chat_type'] = url_response['result']["chat"]["type"]
        send_elements['is_bot'] = url_response['result']["from"]["is_bot"]
        # check if we're dealing with a message or doc or photo
        if url_response['result'].get('text'):
            send_elements['message'] = url_response['result']["text"]
        elif url_response['result'].get('caption'):
            send_elements['message'] = url_response['result']["caption"]
        return send_elements
    # ------ end: extract content of outgoing messages

    # ------ send messages
    def build_keyboard(items, resize_keyboard=True, inline_keyboard=None):
        keyboard = [[item] for item in items]
        reply_markup = {"keyboard": keyboard, "one_time_keyboard": True, "resize_keyboard": resize_keyboard}
        return json.dumps(reply_markup)

    def build_inline_keyboard(keyboard):
        #reply_markup = {"text": "Ich habe das Video angesehen.", "callback_data": "start - watched intro 1"}
        reply_markup = keyboard
        return json.dumps(reply_markup)

    def send_photo(send_elements, start_time=None):
        #photo, chat_id, caption=None, reply_markup=None
        url = URL + "sendPhoto?photo={}&chat_id={}&parse_mode=HTML".format(send_elements["photo"], send_elements["chat_id"])
        if send_elements["message"]:
            url += "&caption={}".format(send_elements["message"])
        if send_elements["keyboard"]:
            url += "&reply_markup={}".format(send_elements["keyboard"])
        else:
            url += "&reply_markup={\"remove_keyboard\":%20true}"
        url_response = Bot.get_json_from_url(url)
        send_elements = Bot.extract_load(send_elements, url_response)
        if start_time is None:
            Bot.save_updates(send_elements)
        else:
            Bot.save_updates(send_elements, start_time)

    def send_document(send_elements, start_time=None):
        #photo, chat_id, caption=None, reply_markup=None
        url = URL + "sendDocument?document={}&chat_id={}&parse_mode=HTML".format(send_elements["photo"], send_elements["chat_id"])
        if send_elements["message"]:
            url += "&caption={}".format(send_elements["message"])
        if send_elements["keyboard"]:
            url += "&reply_markup={}".format(send_elements["keyboard"])
        else:
            url += "&reply_markup={\"remove_keyboard\":%20true}"
        url_response = Bot.get_json_from_url(url)
        send_elements = Bot.extract_load(send_elements, url_response)
        if start_time is None:
            Bot.save_updates(send_elements)
        else:
            Bot.save_updates(send_elements, start_time)

    def send_video(send_elements, start_time=None):
        #photo, chat_id, caption=None, reply_markup=None
        url = URL + "sendVideo?video={}&chat_id={}&parse_mode=HTML".format(send_elements["photo"], send_elements["chat_id"])
        if send_elements["message"]:
            url += "&caption={}".format(send_elements["message"])
        # check if keyboard is there or remove
        if send_elements["keyboard"]:
            url += "&reply_markup={}".format(send_elements["keyboard"])
        else:
            url += "&reply_markup={\"remove_keyboard\":%20true}"
        url_response = Bot.get_json_from_url(url)
        send_elements = Bot.extract_load(send_elements, url_response)
        if start_time is None:
            Bot.save_updates(send_elements)
        else:
            Bot.save_updates(send_elements, start_time)

    def send_message(send_elements, start_time=None):
        parsed_message = urllib.parse.quote_plus(send_elements["message"])
        url = URL + "sendMessage?text={}&chat_id={}&parse_mode=HTML".format(parsed_message, send_elements["chat_id"])
        # when sending the privacy policy, don't show the preview
        if 'datenschutz' in send_elements["message"] or 'Wähle einen Artikel:' in send_elements["message"]:
            url = url + "&disable_web_page_preview=true"
        # remove keyboard from the background if no new keyboard is provided
        if send_elements["keyboard"]:
            url += "&reply_markup={}".format(send_elements["keyboard"])
        else:
            url += "&reply_markup={\"remove_keyboard\":%20true}"
        # send message and save response
        created_at_self = Bot.save_updates(send_elements, start_time)
        url_response = Bot.get_json_from_url(url)
        send_elements = Bot.extract_load(send_elements, url_response)
        Bot.update_updates(send_elements, created_at_self)
    # ------ end: send messages

    # ------ handle updates
    def handle_updates(self, first_name, chat_id, patient_intent, patient_message, start_time=None):
        try:
            # send_elements holds the response from the bot
            # send_elements(created_at, message_id, message, intent, keyboard, user_id, first_name, chat_id, chat_title, chat_type, is_bot)
            send_elements = {'update_id': None, 'created_at': None, 'message_id': None, 'message': None, 'intent': None, 'keyboard': None, 'resize_keyboard': None, 'inline_keyboard': None, 'user_id': None, 'first_name': None, 'chat_id': None, 'chat_title': None, 'chat_type': None, 'bot_command': None, 'key_value': None, 'photo': None, 'is_bot': None, 'language_code': None, 'callback_query_id': None, 'group_chat_created': None, 'new_chat_participant_id': None}
            send_elements["intent"] = patient_intent
            send_elements["chat_id"] = chat_id
            print(patient_intent)
            if patient_intent in ['/tagebuch']:
                print('in here')
            #####
                send_elements["message"], send_elements["keyboard"], send_elements["resize_keyboard"], send_elements["inline_keyboard"], send_elements["photo"], send_elements["key_value"], send_elements["intent"] = DialogueBot.find_response(patient_intent, chat_id, first_name=first_name)
                # if keyboard needed, get it
                if send_elements["inline_keyboard"]:
                    send_elements["keyboard"] = Bot.build_inline_keyboard(send_elements["inline_keyboard"])
                elif send_elements["keyboard"]:
                    send_elements["keyboard"] = Bot.build_keyboard(send_elements["keyboard"], send_elements["resize_keyboard"])

                if send_elements["key_value"] and "p_" in send_elements["key_value"]:
                    Bot.add_to_profile(chat_id, send_elements["key_value"].split("_",1)[1])
                    DataBot.find_key_values(limit=5)


            if send_elements["photo"]:
                file_type = os.path.splitext(send_elements["photo"])[1]
                if file_type == ".gif":
                    Bot.send_document(send_elements, start_time)
                elif file_type == ".pdf":
                    Bot.send_document(send_elements, start_time)
                elif file_type == ".mp4":
                    Bot.send_video(send_elements, start_time)
                else:
                    Bot.send_photo(send_elements, start_time)
            else:
                Bot.send_message(send_elements, start_time)
        except Exception as e:
            # add error to error table - better would be queue
            print(e)
            created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            context = 'issue_with_update_handler'
            chat_id = chat_id
            db.add_error(created_at, chat_id, context, str(e))
    # ------ end: handle updates
