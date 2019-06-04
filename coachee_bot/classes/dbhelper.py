#!/usr/bin/python3.6
# coding: utf8

from time import sleep
from sqlalchemy import *

import sys #required because files in other folder
sys.path.append('../')
import config


class DBHelper:
    def __init__(self):
        engine = create_engine(config.POSTGRES)
        metadata = MetaData(engine)
        self.conn = engine.connect()

    def setup(self):
        print("creating table")
        coachee_update_stmt = 'CREATE TABLE IF NOT EXISTS coachee_updates (id serial primary key, message_id int, created_at timestamp, message text, intent text, telegram_id int, chat_id int, chat_type text, bot_command text, key_value text, is_bot boolean, callback_query_id bigint, group_chat_created int, new_chat_participant_id int, update_id int, time_to_send float)'
        coachee_user_stmt = 'CREATE TABLE IF NOT EXISTS coachee_users (id serial primary key, telegram_id int, first_name text, created_at timestamp, is_bot boolean, language_code text)'
        coachee_error_stmt = 'CREATE TABLE IF NOT EXISTS coachee_errors (id serial primary key, created_at timestamp, chat_id varchar, context text, e text)'
        update_stmt = 'CREATE TABLE IF NOT EXISTS updates (id serial primary key, message_id int, created_at timestamp, message text, intent text, telegram_id int, chat_id int, chat_type text, bot_command text, key_value text, is_bot boolean, callback_query_id bigint, group_chat_created int, new_chat_participant_id int, update_id int, time_to_send float)'
        user_stmt = 'CREATE TABLE IF NOT EXISTS users (id serial primary key, telegram_id int, first_name text, created_at timestamp, is_bot boolean, language_code text)'
        trigger_stmt = 'CREATE TABLE IF NOT EXISTS triggers (id serial primary key, telegram_id int, chat_id int, trigger_value text, trigger_time text, trigger_day text, trigger_specific text, created_at timestamp)'
        keyvalue_stmt = 'CREATE TABLE IF NOT EXISTS key_values (id serial primary key, telegram_id int, chat_id int, key_value text, value text, created_at timestamp)'
        dialoguestmt = 'CREATE TABLE IF NOT EXISTS dialogues (id serial primary key, intent text, np_array text)'
        skillstmt = 'CREATE TABLE IF NOT EXISTS skills (id serial primary key, name text, intent_identifier text, created_at timestamp)'
        letterstmt = 'CREATE TABLE IF NOT EXISTS letters (id serial primary key, name text, url text, created_at timestamp)'
        menustmt = 'CREATE TABLE IF NOT EXISTS user_menus (id serial primary key, telegram_id int, chat_id int, category text, value text, created_at timestamp)'
        progress_stmt = 'CREATE TABLE IF NOT EXISTS user_progress (id serial primary key, telegram_id int, chat_id int, category text, component text, started_at timestamp, completed_at timestamp, finished boolean, created_at timestamp)'
        error_stmt = 'CREATE TABLE IF NOT EXISTS errors (id serial primary key, created_at timestamp, chat_id varchar, context text, e text)'
        upkeep_stmt = 'CREATE TABLE IF NOT EXISTS upkeep (id serial primary key, created_at timestamp, pointer text)'
        files_stmt = 'CREATE TABLE IF NOT EXISTS files (id serial primary key, telegram_id int, chat_id int, intent text, key_value text, file text, created_at timestamp)'
        ididx = 'CREATE INDEX IF NOT EXISTS idIndex ON updates (id ASC)'
        userididx = 'CREATE INDEX IF NOT EXISTS idUserIndex ON users (id ASC)'
        self.conn.execute(coachee_update_stmt)
        self.conn.execute(coachee_user_stmt)
        self.conn.execute(coachee_error_stmt)
        self.conn.execute(update_stmt)
        self.conn.execute(user_stmt)
        self.conn.execute(trigger_stmt)
        self.conn.execute(keyvalue_stmt)
        self.conn.execute(dialoguestmt)
        self.conn.execute(skillstmt)
        self.conn.execute(letterstmt)
        self.conn.execute(menustmt)
        self.conn.execute(progress_stmt)
        self.conn.execute(error_stmt)
        self.conn.execute(upkeep_stmt)
        self.conn.execute(files_stmt)
        self.conn.execute(ididx)
        self.conn.execute(userididx)

    ##### add functions
    # add update_id, created_at, message_id, message, telegram_id, chat_id, chat_type, callback_query_id
    def add_update(self, message_id, created_at, message, intent, telegram_id, chat_id, chat_type, bot_command, key_value, is_bot, callback_query_id, group_chat_created, new_chat_participant_id, update_id, time_to_send=None):
        if time_to_send is None:
            stmt = 'INSERT INTO coachee_updates (message_id, created_at, message, intent, telegram_id, chat_id, chat_type, bot_command, key_value, is_bot, callback_query_id, group_chat_created, new_chat_participant_id, update_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
            args = [message_id, created_at, message, intent, telegram_id, chat_id, chat_type, bot_command, key_value, is_bot, callback_query_id, group_chat_created, new_chat_participant_id, update_id]
        else:
            stmt = 'INSERT INTO coachee_updates (message_id, created_at, message, intent, telegram_id, chat_id, chat_type, bot_command, key_value, is_bot, callback_query_id, group_chat_created, new_chat_participant_id, update_id, time_to_send) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
            args = [message_id, created_at, message, intent, telegram_id, chat_id, chat_type, bot_command, key_value, is_bot, callback_query_id, group_chat_created, new_chat_participant_id, update_id, time_to_send]
        try:
            self.conn.execute(stmt, args)
        except Exception as e:
            print(e)

    # add telegram_id, first_name, created_at, is_bot, language_code
    def add_user(self, telegram_id, first_name, created_at, is_bot, language_code):
        stmt = 'INSERT INTO coachee_users (telegram_id, first_name, created_at, is_bot, language_code) VALUES (%s, %s, %s, %s, %s)'
        args = [telegram_id, first_name, created_at, is_bot, language_code]
        self.conn.execute(stmt, args)

    # add telegram_id, chat_id, intent, key_value, created_at
    def add_key_value(self, telegram_id, chat_id, key_value, value, created_at):
        stmt = 'INSERT INTO key_values (telegram_id, chat_id, key_value, value, created_at) VALUES (%s, %s, %s, %s, %s)'
        args = [telegram_id, chat_id, key_value, value, created_at]
        self.conn.execute(stmt, args)

    # add telegram_id, chat_id, intent, key_value, created_at
    def add_trigger(self, telegram_id, chat_id, trigger_value, trigger_time, trigger_day, trigger_specific, created_at):
        stmt = 'INSERT INTO triggers (telegram_id, chat_id, trigger_value, trigger_time, trigger_day, trigger_specific, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)'
        args = [telegram_id, chat_id, trigger_value, trigger_time, trigger_day, trigger_specific, created_at]
        self.conn.execute(stmt, args)

    def add_user_progress(self, telegram_id, chat_id, category, component, started_at, completed_at, created_at):
        stmt = 'INSERT INTO user_progress (telegram_id, chat_id, category, component, started_at, completed_at, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s)'
        args = [telegram_id, chat_id, category, component, started_at, completed_at, created_at]
        self.conn.execute(stmt, args)

    def add_to_profile(self, telegram_id, chat_id, category, value, created_at):
        stmt = 'INSERT INTO user_menus (telegram_id, chat_id, category, value, created_at) VALUES (%s, %s, %s, %s, %s)'
        args = [telegram_id, chat_id, category, value, created_at]
        self.conn.execute(stmt, args)

    def add_error(self, created_at, chat_id, context, e):
        stmt = 'INSERT INTO coachee_errors (created_at, chat_id, context, e) VALUES (%s, %s, %s, %s)'
        args = [created_at, chat_id, context, e]
        self.conn.execute(stmt, args)

    def add_upkeep(self, created_at, pointer):
        stmt = 'INSERT INTO upkeep (created_at, pointer) VALUES (%s, %s)'
        args = [created_at, pointer]
        self.conn.execute(stmt, args)

    def add_file(self, telegram_id, chat_id, intent, key_value, file, created_at):
        stmt = 'INSERT INTO files (telegram_id, chat_id, intent, key_value, file, created_at) VALUES (%s, %s, %s, %s, %s, %s)'
        args = [telegram_id, chat_id, intent, key_value, file, created_at]
        try:
            self.conn.execute(stmt, args)
        except Exception as e:
            print(e)
    ##### end: add functions

    ##### update functions
    def update_update(self, created_at_self, message_id, created_at, message, intent, telegram_id, chat_id, chat_type, bot_command, key_value, is_bot, callback_query_id, group_chat_created, new_chat_participant_id, update_id):
        stmt = 'UPDATE coachee_updates SET message_id = %s, created_at = %s, message = %s, intent = %s, telegram_id = %s, chat_id = %s, chat_type = %s, bot_command = %s, key_value = %s, is_bot = %s, callback_query_id = %s, group_chat_created = %s, new_chat_participant_id = %s, update_id = %s WHERE created_at = %s AND chat_id = %s AND message = %s'
        #stmt = 'SELECT * from updates WHERE created_at = ? AND chat_id = ? AND message = ?'
        args = [message_id, created_at, message, intent, telegram_id, chat_id, chat_type, bot_command, key_value, is_bot, callback_query_id, group_chat_created, new_chat_participant_id, update_id, created_at_self, chat_id, message]
        try:
            self.conn.execute(stmt, args)
        except Exception as e:
            print(e)

    def update_user_progress(self, completed_at, telegram_id, component):
        stmt = 'UPDATE user_progress SET completed_at = %s WHERE telegram_id = %s AND component = %s'
        args = [completed_at, telegram_id, component]
        try:
            self.conn.execute(stmt, args)
        except Exception as e:
            print(e)
    ##### end: update functions

    ##### check functions
    def check_key_values(self, telegram_id, chat_id, key_value, value, created_at):
        stmt = 'SELECT COUNT(*) FROM key_values WHERE telegram_id = %s AND chat_id = %s AND key_value = %s AND value = cast(%s as text) AND created_at = %s'
        args = [telegram_id, chat_id, key_value, value, created_at]
        return self.conn.execute(stmt, args).fetchall()[0][0]

    def check_triggers(self, telegram_id, chat_id, trigger_value, trigger_day, trigger_time, created_at=None):
        if created_at is None:
            stmt = 'SELECT COUNT(*) FROM triggers WHERE telegram_id = %s AND chat_id = %s AND trigger_value = %s AND trigger_day = %s AND trigger_time = %s'
            args = [telegram_id, chat_id, trigger_value, trigger_day, trigger_time]
        else:
            stmt = 'SELECT COUNT(*) FROM triggers WHERE telegram_id = %s AND chat_id = %s AND trigger_value = %s AND trigger_day = %s AND trigger_time = %s AND created_at = %s'
            args = [telegram_id, chat_id, trigger_value, trigger_day, trigger_time, created_at]
        return self.conn.execute(stmt, args).fetchall()[0][0]

    def check_user(self, telegram_id):
        stmt = 'SELECT COUNT(*) FROM coachee_users WHERE telegram_id = %s'
        args = [telegram_id]
        return self.conn.execute(stmt, args).fetchall()[0][0]

    def check_profile(self, telegram_id, chat_id, category, value):
        stmt = 'SELECT COUNT(*) FROM user_menus WHERE telegram_id = %s AND chat_id = %s AND category = %s AND value = %s'
        args = [telegram_id, chat_id, category, value]
        return self.conn.execute(stmt, args).fetchall()[0][0]

    def check_user_progress(self, telegram_id, component):
        stmt = 'SELECT COUNT(*) FROM user_progress WHERE telegram_id = %s AND component = %s'
        args = [telegram_id, component]
        return self.conn.execute(stmt, args).fetchall()[0][0]

    def check_files(self, telegram_id, intent, key_value, file):
        if key_value is None:
            stmt = 'SELECT COUNT(*) FROM files WHERE telegram_id = %s AND intent = %s AND key_value is %s AND file = %s'
        else:
            stmt = 'SELECT COUNT(*) FROM files WHERE telegram_id = %s AND intent = %s AND key_value = %s AND file = %s'
        args = [telegram_id, intent, key_value, file]
        return self.conn.execute(stmt, args).fetchall()[0][0]
    ##### end: check functions

    ##### get functions
    def get_user_since(self, telegram_id):
        stmt = "SELECT min(created_at) FROM coachee_updates WHERE telegram_id = %s"
        args = [telegram_id]
        try:
            return self.conn.execute(stmt, args).fetchall()[0][0]
        except Exception as e:
            print(e)

    def get_users(self):
        stmt = "SELECT telegram_id, first_name FROM coachee_users GROUP BY 1, 2"
        try:
            return self.conn.execute(stmt).fetchall()
        except Exception as e:
            print(e)

    def get_last_message(self, chat_id, is_bot=None):
        if is_bot is None:
            stmt = 'SELECT intent, message, key_value FROM coachee_updates WHERE chat_id = %s ORDER BY id DESC LIMIT 1'
            args = [chat_id]
        else:
            stmt = 'SELECT intent, message, key_value FROM coachee_updates WHERE chat_id = %s AND is_bot = cast(%s as boolean) ORDER BY id DESC LIMIT 1'
            args = [chat_id, is_bot]

        result = self.conn.execute(stmt, args).fetchall()
        # if there are no bot messages yet, return None
        if result:
            return self.conn.execute(stmt, args).fetchall()[0]
        else:
            return None

    def get_key_values_from_updates(self, key_value=None, is_bot=None, limit=None):
        if limit is None:
            if key_value is None and is_bot is None:
                stmt = 'SELECT telegram_id, chat_id, message, key_value, is_bot, created_at, intent FROM coachee_updates WHERE key_value is not Null AND is_bot = cast(0 as boolean) ORDER BY id DESC'
                args = []
            elif key_value is not None and is_bot is None:
                stmt = 'SELECT telegram_id, chat_id, message, key_value, is_bot, created_at, intent FROM coachee_updates WHERE key_value = %s AND is_bot = cast(0 as boolean) ORDER BY id DESC'
                args = [key_value]
            else:
                stmt = 'SELECT telegram_id, chat_id, message, key_value, is_bot, created_at, intent FROM coachee_updates WHERE key_value = %s AND is_bot = cast(%s as boolean) ORDER BY id DESC'
                args = [key_value, is_bot, ]
        else:
            if key_value is None and is_bot is None:
                stmt = 'SELECT telegram_id, chat_id, message, key_value, is_bot, created_at, intent FROM coachee_updates WHERE key_value is not Null AND is_bot = cast(0 as boolean) ORDER BY id DESC LIMIT %s'
                args = [limit]
            elif key_value is not None and is_bot is None:
                stmt = 'SELECT telegram_id, chat_id, message, key_value, is_bot, created_at, intent FROM coachee_updates WHERE key_value = %s AND is_bot = cast(0 as boolean) ORDER BY id DESC LIMIT %s'
                args = [key_value, limit]
            else:
                stmt = 'SELECT telegram_id, chat_id, message, key_value, is_bot, created_at, intent FROM coachee_updates WHERE key_value = %s AND is_bot = cast(%s as boolean) ORDER BY id DESC LIMIT %s'
                args = [key_value, is_bot, limit]

        try:
            return self.conn.execute(stmt, args).fetchall()
        except Exception as e:
            print(e)

    def get_first_name(self, telegram_id):
        stmt = 'SELECT first_name FROM coachee_users WHERE telegram_id = %s'
        args = [telegram_id]
        try:
            return self.conn.execute(stmt, args).fetchall()[0][0]
        except Exception as e:
            print(e)

    def get_trigger_values(self):
        stmt = 'SELECT telegram_id, chat_id, trigger_value, trigger_time, trigger_day, trigger_specific, created_at FROM triggers ORDER BY id DESC'
        args = []
        try:
            return self.conn.execute(stmt, args).fetchall()
        except Exception as e:
            print(e)

    def get_key_values(self, key_value=None, chat_id=None, limit=None):
        if key_value is None and chat_id is None and limit is None:
            stmt = 'SELECT * FROM key_values ORDER BY created_at DESC'
            args = []
        elif key_value is not None and chat_id is None and limit is None:
            stmt = 'SELECT * FROM key_values WHERE key_value = %s ORDER BY created_at DESC'
            args = [key_value]
        elif key_value is None and chat_id is None and limit is not None:
            stmt = 'SELECT * FROM key_values ORDER BY created_at DESC LIMIT %s'
            args = [limit]
        elif key_value is not None and chat_id is None and limit is not None:
            stmt = 'SELECT * FROM key_values WHERE key_value = %s ORDER BY created_at DESC LIMIT %s'
            args = [key_value, limit]
        elif key_value is not None and chat_id is not None and limit is None:
            stmt = 'SELECT * FROM key_values WHERE key_value = %s AND chat_id = %s ORDER BY created_at DESC'
            args = [key_value, chat_id]
        else:
            stmt = 'SELECT * FROM key_values WHERE key_value = %s AND chat_id = %s ORDER BY created_at DESC LIMIT %s'
            args = [key_value, chat_id, limit]
        try:
            return self.conn.execute(stmt, args).fetchall()
        except Exception as e:
            print(e)

    def get_user_menu(self, menu_type, chat_id):
        if menu_type != 'category':
            stmt = "SELECT value FROM user_menus WHERE (category = %s OR category = 'zurueck') AND chat_id = %s GROUP BY value"
            args = [menu_type, chat_id]
        else:
            stmt = "SELECT category FROM user_menus WHERE chat_id = %s GROUP BY category"
            args = [chat_id]
        try:
            return self.conn.execute(stmt, args).fetchall()
        except Exception as e:
            print(e)

    def get_letter(self, name):
        stmt = "SELECT url FROM letters WHERE name = %s ORDER BY id DESC LIMIT 1"
        args = [name]
        try:
            return self.conn.execute(stmt, args).fetchall()[0][0]
        except Exception as e:
            print(e)

    def get_user_progress(self, chat_id):
        stmt = "SELECT * FROM user_progress WHERE chat_id = %s AND completed_at IS NOT Null ORDER BY id DESC"
        args = [chat_id]
        try:
            return self.conn.execute(stmt, args).fetchall()
        except Exception as e:
            print(e)

    def get_files(self):
        stmt = "SELECT telegram_id, chat_id, message, key_value, intent, created_at FROM coachee_updates WHERE message like 'photo: %%' ORDER BY id DESC"
        args = []
        try:
            return self.conn.execute(stmt, args).fetchall()
        except Exception as e:
            print(e)

    def get_running_challenges(self, telegram_id=None):
        if telegram_id is None:
            stmt = "SELECT telegram_id, chat_id, component, started_at FROM user_progress WHERE category = 'challenge' AND completed_at is Null ORDER BY started_at LIMIT 3"
            args = [telegram_id]
        else:
            stmt = "SELECT telegram_id, chat_id, component, started_at FROM user_progress WHERE telegram_id = %s AND category = 'challenge' AND completed_at is Null ORDER BY started_at LIMIT 3"
            args = [telegram_id]
        try:
            return self.conn.execute(stmt, args).fetchall()
        except Exception as e:
            print(e)
    ##### end: get functions

    ##### delete functions
    def delete_from_triggers(self, telegram_id, trigger_value, trigger_day, created_at):
        stmt = 'DELETE FROM triggers WHERE telegram_id = %s AND trigger_value = %s AND trigger_day = %s AND created_at = %s'
        #stmt = 'SELECT * from updates WHERE created_at = ? AND chat_id = ? AND message = ?'
        args = [telegram_id, trigger_value, trigger_day, created_at]
        try:
            self.conn.execute(stmt, args)
        except Exception as e:
            print(e)

    ##### DialogueBot
    def add_dialogue(self, intent, np_array):
        stmt = 'INSERT INTO dialogues (intent, np_array) VALUES (%s, %s)'
        args = [intent, np_array]
        try:
            self.conn.execute(stmt, args)
        except Exception as e:
            print(e)

    def get_dialogue(self, intent_identifier):
        stmt = "SELECT * FROM dialogues WHERE intent = %s ORDER BY id DESC"
        args = [intent_identifier]
        # if there are no matches, return None
        result = self.conn.execute(stmt, args).fetchall()
        if result:
            return self.conn.execute(stmt, args).fetchall()
        else:
            return None

    def wipe_dialogues(self):
        stmt = "DELETE FROM dialogues"
        # if there are no matches, return None
        result = self.conn.execute(stmt)
    ##### End: DialogueBot
