#!/usr/bin/python3.6
# coding: utf8
import logging
import requests
import json
import datetime
import urllib
import os

import sys #required because files in other folder
sys.path.append('../Handler/')
from db_bot import DBBot
from dialogue_bot import DialogueBot

import sys #required because files in parent folder
sys.path.append('../')
import config

TOKEN = config.TELEGRAM_TOKEN
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
DBBot = DBBot()
DialogueBot = DialogueBot()

class Bot:

# ------ process incoming messages
    def get_json_from_url(url):
        response = requests.get(url)
        content = response.content.decode("utf8")
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

    # for handling inline buttons
    def answer_callback(callback_query_id, text=None):
        url = URL + "answerCallbackQuery?callback_query_id={}".format(callback_query_id)
        if text:
            url += "&text={}".format(text)
        Bot.get_json_from_url(url)
# ------ end: process incoming messages

# ------ extract content of incoming messages
    # key function to save to database
    def save_messages(message_elements):
        # set time when message was saved to db
        message_elements['received_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # check if user is in db already; if not, add him
        ## possible improvement: add a global variable later to avoid checking the db at every message
        if message_elements['is_bot'] is not None:
            if DBBot.check_user(message_elements['user_id']) == 0:
                # add user_id, first_name, created_at, is_bot, language_code
                DBBot.add_user(message_elements['user_id'], message_elements['first_name'], message_elements['created_at'], message_elements['received_at'], message_elements['is_bot'], message_elements['language_code'])
                logging.info(f"New user created: {message_elements['user_id']}")

        # save message to db
        try:
            DBBot.add_message(message_elements['message_id'], message_elements['created_at'], message_elements['received_at'], message_elements['message'], message_elements['intent'], message_elements['user_id'], message_elements['chat_id'], message_elements['chat_type'], message_elements['bot_command'], message_elements['key_value'], message_elements['is_bot'], message_elements['callback_query_id'], message_elements['group_chat_created'], message_elements['new_chat_participant_id'], message_elements['update_id'])
        except Exception as e:
            logging.exception("Exception in add_message")

    # invoked in extract_updates()
    def check_content(update):
        content = None
        # check whether we're dealing with a message or a callback
        if update.get('message') is not None:
            if update["message"].get('group_chat_created') is None or update["message"].get('new_chat_participant') is None or update["message"].get('left_chat_participant') is None:
                content = 'extract_message'
            else:
                print('do_not_extract_event')
                content = 'do_not_extract'
        elif update.get('callback_query') is not None:
            content = 'extract_callback'
        return content

    # invoked in extract_updates()
    def extract_message(message_elements, message):
        # save attributes
        message_elements['created_at'] = datetime.datetime.fromtimestamp(int(message["date"])).strftime('%Y-%m-%d %H:%M:%S')
        message_elements['message_id'] = message["message_id"]
        # if the message has text, save it
        if message.get('text') is not None:
            message_elements['message'] = message["text"]
        elif message.get('document') is not None and message["from"]["is_bot"] is False:
            message_elements['message'] = 'photo: ' + message["document"]["file_id"]
        # check if user sent a meal picture (but make sure that bot photos are sent through!)
        elif message.get('photo') is not None and message["from"]["is_bot"] is False:
            try:
                message_elements['message'] = 'photo: ' + message["photo"][3]["file_id"]
                message_elements['key_value'] = 'user_photo'
            except:
                message_elements['message'] = 'photo: ' + message["photo"][0]["file_id"]
                message_elements['key_value'] = 'user_photo'
        message_elements['user_id'] = message["from"]["id"]
        message_elements['first_name'] = message["from"]["first_name"]
        message_elements['chat_id'] = message["chat"]["id"]
        message_elements['chat_type'] = message["chat"]["type"]
        # if the user sends a bot_command (e.g. /start or /check_in), save it
        if message.get('entities') is not None:
            for entity in message["entities"]:
                message_elements['bot_command'] = entity["type"]
                message_elements['key_value'] = message_elements["message"].lower()[1:]+'_start'
        message_elements['is_bot'] = message["from"]["is_bot"]
        # if the message has a language code, save it
        if message["from"].get('language_code') is not None:
            message_elements['language_code'] = message["from"]["language_code"]
        return message_elements

    # invoked in extract_updates() - for handling inline buttons
    def extract_callback(message_elements, message):
        # save callback_query_id
        message_elements['callback_query_id'] = message["id"]
        # remove loading button on the client
        Bot.answer_callback(message_elements['callback_query_id'])
        # save remaining parameters
        message_elements['created_at'] = datetime.datetime.fromtimestamp(int(message["message"]["date"])).strftime('%Y-%m-%d %H:%M:%S')
        #update_elements['created_at'] = created_at.replace(tzinfo=pytz.utc).astimezone(local_tz).strftime('%Y-%m-%d %H:%M:%S')
        message_elements['message_id'] = message["message"]["message_id"]
        message_elements['message'] = message["data"]
        # if the callback is a bot command, set it
        if "/" in message["data"] and "http" not in message["data"]:
            message_elements['bot_command'] = "bot_command"
            message_elements['key_value'] = message_elements["message"].lower()[1:]+'_start'
        message_elements['user_id'] = message["from"]["id"]
        message_elements['first_name'] = message["from"]["first_name"]
        message_elements['chat_id'] = message["message"]["chat"]["id"]
        # if the chat has a title, save it
        if message["message"]["chat"].get('title') is not None:
            message_elements['chat_title'] = message["message"]["chat"]["title"]
        message_elements['chat_type'] = message["message"]["chat"]["type"]
        message_elements['is_bot'] = message["from"]["is_bot"]
        # if the message has a language code, save it
        if message["from"].get('language_code') is not None:
            message_elements['language_code'] = message["from"]["language_code"]
        return message_elements

    def get_intent(message_elements):
        # set bot_command as intent
        if message_elements["bot_command"] == 'bot_command':
            message_elements["intent"] = message_elements["message"].lower()
        # if there is no bot command, continue the discussion that is under way or set 'open_conversation'
        else:
            # get the intent and the key value of the last bot message
            last_bot_message = DBBot.get_last_message(message_elements["chat_id"], 1)
            # it is possible that there are no bot messages yet, therefore check if None
            if last_bot_message:
                last_intent, last_msg, last_key_value = last_bot_message[0], last_bot_message[1], last_bot_message[2]
                if message_elements['key_value'] in ('user_photo', 'meal_entry'):
                    message_elements["intent"] = config.user_photo
                elif last_intent == 'end_conversation' or last_intent is None:
                    message_elements["intent"] = 'open_conversation'
                else:
                    message_elements["intent"] = last_intent
                    if message_elements["key_value"] != 'user_photo':
                        message_elements["key_value"] = last_key_value
            else:
                message_elements["intent"] = 'open_conversation'
        return message_elements

    # main extract_ function that defines where an update is routed towards
    def extract_updates(self, updates):
        for update in updates["result"]:
            # message container for incoming and outgoing msgs
            message_elements = {'update_id': None, 'created_at': None, 'received_at': None, 'message_id': None, 'message': None, 'intent': None, 'keyboard': None, 'user_id': None, 'first_name': None, 'chat_id': None, 'chat_title': None, 'chat_type': None, 'bot_command': None, 'key_value': None, 'img': None, 'is_bot': None, 'language_code': None, 'callback_query_id': None, 'group_chat_created': None, 'new_chat_participant_id': None}

            # check whether we're dealing with a message, a callback or not-to-be-extracted content
            content = Bot.check_content(update)
            if content not in ['do_not_extract']:
                if content == 'extract_message':
                    message_elements = Bot.extract_message(message_elements, update['message'])
                elif content == 'extract_callback':
                    message_elements = Bot.extract_callback(message_elements, update['callback_query'])
                message_elements = Bot.get_intent(message_elements)
                Bot.save_messages(message_elements)
                return message_elements
# ------ end: extract content of incoming messages

# ------ start: send messages
    def send_message(message_elements):
        parsed_message = urllib.parse.quote_plus(message_elements["message"])
        url = URL + "sendMessage?text={}&chat_id={}&parse_mode=HTML&disable_web_page_preview=true".format(parsed_message, message_elements["chat_id"])
        # remove keyboard from the background if no new keyboard is provided
        if message_elements["keyboard"]:
            url += "&reply_markup={}".format(message_elements["keyboard"])
        else:
            url += "&reply_markup={\"remove_keyboard\":%20true}"
        # send message and save response
        url_response = Bot.get_json_from_url(url)
        message_elements = Bot.extract_message(message_elements, url_response["result"])
        Bot.save_messages(message_elements)

    def send_photo(message_elements):
        #photo, chat_id, caption=None, reply_markup=None
        url = URL + "sendPhoto?photo={}&chat_id={}&parse_mode=HTML".format(message_elements["img"], message_elements["chat_id"])
        if message_elements["message"]:
            url += "&caption={}".format(message_elements["message"])
        if message_elements["keyboard"]:
            url += "&reply_markup={}".format(message_elements["keyboard"])
        else:
            url += "&reply_markup={\"remove_keyboard\":%20true}"
        url_response = Bot.get_json_from_url(url)
        message_elements = Bot.extract_message(message_elements, url_response["result"])
        Bot.save_messages(message_elements)

    # for gifs and pdfs
    def send_document(message_elements):
        #photo, chat_id, caption=None, reply_markup=None
        url = URL + "sendDocument?document={}&chat_id={}&parse_mode=HTML".format(message_elements["img"], message_elements["chat_id"])
        if message_elements["message"]:
            url += "&caption={}".format(message_elements["message"])
        if message_elements["keyboard"]:
            url += "&reply_markup={}".format(message_elements["keyboard"])
        else:
            url += "&reply_markup={\"remove_keyboard\":%20true}"
        url_response = Bot.get_json_from_url(url)
        message_elements = Bot.extract_message(message_elements, url_response["result"])
        Bot.save_messages(message_elements)
# ------ end: send messages


# ------ handle updates
    def handle_updates(self, first_name, chat_id, intent, message):
        # message container for incoming and outgoing msgs
        message_elements = {'update_id': None, 'created_at': None, 'received_at': None, 'message_id': None, 'message': None, 'intent': None, 'keyboard': None, 'user_id': None, 'first_name': None, 'chat_id': None, 'chat_title': None, 'chat_type': None, 'bot_command': None, 'key_value': None, 'callback_url': None, 'img': None, 'is_bot': None, 'language_code': None, 'callback_query_id': None, 'group_chat_created': None, 'new_chat_participant_id': None}

        message_elements["intent"] = intent
        message_elements["chat_id"] = chat_id
        ##### TO DO: catch-all until fixed:
        if intent in ['open_conversation', 'end_conversation']:
            message_elements["message"], message_elements["keyboard"], message_elements["callback_url"], message_elements["img"], message_elements["key_value"], message_elements["intent"] = DialogueBot.find_response("/befehle", chat_id, last_user_message="/befehle", last_bot_message="✏")
            logging.info(f'Open dialogue started by {chat_id}')
        ##### end catch-all
        else:
            message_elements["message"], message_elements["keyboard"], message_elements["callback_url"], message_elements["img"], message_elements["key_value"], message_elements["intent"] = DialogueBot.find_response(intent, chat_id)
        
        # create keyboard
        if message_elements["keyboard"]:
            message_elements["keyboard"] = Bot.build_keyboard(message_elements["keyboard"], message_elements["callback_url"])

        # check for photo, doc or other
        if message_elements["img"]:
            file_type = os.path.splitext(message_elements["img"])[1]
            if file_type == ".gif" or file_type == ".pdf":
                Bot.send_document(message_elements)
            else:
                Bot.send_photo(message_elements)
        else:
            Bot.send_message(message_elements)


    def build_keyboard(keyboard, callback_url):
        inline_keyboard = []
        # needed to make sure that not more than 2 buttons are allowed side-by-side
        temp_keyboard = []
        # create correct format for inline_keyboard, e.g.: {"inline_keyboard":[[{"text": "Hello", "callback_url": "Hello", "url": "", "callback_data": "Hello"},{"text": "No", "callback_url": "Google", "url": "http://www.google.com/"}]]}
        n_items = len(keyboard)-1
        for num, row in enumerate(keyboard):
            # check whether it is a callback (internal dialogue) or url (external)
            if "http" in callback_url[num]:
                inline_type = "url"
            else:
                inline_type = "callback_data"    
            temp_keyboard.append({"text": keyboard[num], inline_type: callback_url[num]})
            # do not allow more than 2 buttons side-by-side
            if (num % 2 == 1) or num == n_items: 
                inline_keyboard.append(temp_keyboard)
                temp_keyboard = []
        reply_markup = {"inline_keyboard": inline_keyboard}
        return json.dumps(reply_markup)
# ------ end: handle updates