#!/usr/bin/python3.6
# coding: utf8
import re
import emoji
import datetime

import numpy as np

import requests
import json
import urllib

from dbhelper import DBHelper

import sys #required because files in parent folder
sys.path.append('../')
import config

db = DBHelper()

class DataBot:

    #### functions to convert from message to db
    # daily job to write new values to db
    def extract_and_map_emojis(self, message):
        emoji_mapper = {'☺': 4, '😄': 5, '😊': 4, '😒': 3, '😔': 2, '😞': 3, '😣': 1, '😨': 2, '😩': 1, '😐': 3}
        used_emoji = ''.join(c for c in message if c in emoji.UNICODE_EMOJI)
        if used_emoji in emoji_mapper:
            score = emoji_mapper[used_emoji]
        else:
            score = None
        return score

    def find_key_values(self, limit=None):
        # get the unique key values
        data = db.get_key_values_from_updates(limit=limit)
        data.reverse()
        for row in data:
            if row[3] == "c_feedback_value":
                if re.findall("\d+", row[2]):
                    value = re.findall("\d+", row[2])[0]
                    key_value = row[3] + ": " + row[6]
                    if db.check_key_values(row[0], row[1], key_value, value, row[5]) == 0:
                        db.add_key_value(row[0], row[1], key_value, value, row[5])
                        print('key_value for {} added'.format(key_value))
            elif "value" in row[3] or "duration" in row[3]:
                if re.findall("\d+\.\d+", row[2]):
                    value = re.findall("\d+\.\d+", row[2])[0]
                    if db.check_key_values(row[0], row[1], row[3], value, row[5]) == 0:
                        db.add_key_value(row[0], row[1], row[3], value, row[5])
                        print('key_value for {} added'.format(row[3]))
                elif re.findall("\d+\,\d+", row[2]):
                    value = re.findall("\d+\,\d+", row[2])[0]
                    value = value.replace(',','.')
                    if db.check_key_values(row[0], row[1], row[3], value, row[5]) == 0:
                        db.add_key_value(row[0], row[1], row[3], value, row[5])
                        print('key_value for {} added'.format(row[3]))
                elif re.findall("\d+", row[2]):
                    value = re.findall("\d+", row[2])[0]
                    if db.check_key_values(row[0], row[1], row[3], value, row[5]) == 0:
                        db.add_key_value(row[0], row[1], row[3], value, row[5])
                        print('key_value for {} added'.format(row[3]))
            elif "mood" in row[3]:
                try:
                    if DataBot.extract_and_map_emojis(row[2]):
                        value = DataBot.extract_and_map_emojis(row[2])
                        if db.check_key_values(row[0], row[1], row[3], value, row[5]) == 0:
                            db.add_key_value(row[0], row[1], row[3], value, row[5])
                            print('key_value for {} added'.format(row[3]))
                except:
                    if DataBot.extract_and_map_emojis(self, row[2]):
                        value = DataBot.extract_and_map_emojis(self, row[2])
                        if db.check_key_values(row[0], row[1], row[3], value, row[5]) == 0:
                            db.add_key_value(row[0], row[1], row[3], value, row[5])
                            print('key_value for {} added'.format(row[3]))
            elif "time" in row[3]:
                # if row[0] == 164570223 or row[0] == 415604082:
                #     continue
                if re.findall("\d+\:\d+", row[2]):
                    value = re.findall("\d+\:\d+", row[2])[0]
                    if db.check_key_values(row[0], row[1], row[3], value, row[5]) == 0:
                        db.add_key_value(row[0], row[1], row[3], value, row[5])
                        print('key_value for {} added'.format(row[3]))
                elif re.findall("\d+\.\d+", row[2]):
                    value = re.findall("\d+\.\d+", row[2])[0]
                    value = value.replace('.',':')
                    if db.check_key_values(row[0], row[1], row[3], value, row[5]) == 0:
                        db.add_key_value(row[0], row[1], row[3], value, row[5])
                        print('key_value for {} added'.format(row[3]))
                elif re.findall("\d+\,\d+", row[2]):
                    value = re.findall("\d+\,\d+", row[2])[0]
                    value = value.replace(',',':')
                    if db.check_key_values(row[0], row[1], row[3], value, row[5]) == 0:
                        db.add_key_value(row[0], row[1], row[3], value, row[5])
                        print('key_value for {} added'.format(row[3]))
                elif re.findall("\d+", row[2]):
                    value = re.findall("\d+", row[2])[0]
                    # add a leading zero and 2 zeros at the end
                    value = value + ':00'
                    if db.check_key_values(row[0], row[1], row[3], value, row[5]) == 0:
                        db.add_key_value(row[0], row[1], row[3], value, row[5])
                        print('key_value for {} added'.format(row[3]))
            elif "motivation" in row[3] or "plan" in row[3] or "c_completed" in row[3] or "user_photo" in row[3] or "meal_entry" in row[3]:
                value = row[2]
                if db.check_key_values(row[0], row[1], row[3], value, row[5]) == 0:
                    db.add_key_value(row[0], row[1], row[3], value, row[5])
                    print('key_value for {} added'.format(row[3]))
            elif "proudMoments" in row[3] or "makeBetter" in row[3] or "change" in row[3]:
                value = row[2]
                if value not in ['Hast du ein Beispiel?', 'Hast du noch ein Beispiel?', 'Alles klar. Ich weiß etwas']:
                    if db.check_key_values(row[0], row[1], row[3], value, row[5]) == 0:
                        db.add_key_value(row[0], row[1], row[3], value, row[5])
                        print('key_value for {} added'.format(row[3]))

    #### functions to convert from db to message
    def convert_to_emoji(self, value):
        emoji_mapper = {5: '😄', 4: '😊', 3: '😒', 2: '😔', 1: '😞'}
        return emoji_mapper[value]

    def convert_to_dow(self, value):
        emoji_mapper = {0: 'Mo', 1: 'Di', 2: 'Mi', 3: 'Do', 4: 'Fr', 5: 'Sa', 6: 'So', 7: 'So'}
        return emoji_mapper[value]

    #### functions to convert from key_value to trigger
    def add_trigger_for_times(self, key_value):
        if key_value == 'wi_time' or key_value == 'wi_time_wknd' or key_value == 'wi_time_wrkday':
            trigger_value = '/wiegen'
            if key_value == 'wi_time_wknd':
                trigger_day = "sat-sun"
            elif key_value == 'wi_time_wrkday':
                trigger_day = "mon-fri"
            else:
                trigger_day = "mon-sun"
        elif key_value == 'ci_time':
            trigger_value = '/check_in'
            trigger_day = "mon-sat"
        data = db.get_key_values(key_value)
        for row in data:
            user_id = row[1]
            chat_id = row[2]
            created_at = row[5]
            trigger_specific = created_at
            # unique for _time values
            trigger_time = row[4]
            # check if user joined today or earlier
            user_since = db.get_user_since(chat_id).date()
            today = datetime.date.today()
            # don't add if a user joined today (to make sure that check in messages don't get triggered on the day of the onboarding)
            if user_since != today:
                # check if already there or add
                if db.check_triggers(user_id, chat_id, trigger_value, trigger_day, trigger_time) == 0:
                    db.add_trigger(user_id, chat_id, trigger_value, trigger_time, trigger_day, None, created_at)
                    print('trigger for {} added'.format(trigger_value))
                # add summary trigger (= ci_time on Sundays)
                if key_value == 'ci_time' and db.check_triggers(user_id, chat_id, '/summary', 'sun', trigger_time) == 0:
                    db.add_trigger(user_id, chat_id, '/summary', trigger_time, 'sun', None, created_at)
                    print('trigger for {} added'.format('/summary'))

    # convert hourly fast to cronjob hours
    def add_trigger_for_fast(self, key_value):
        if key_value in ['f_duration']:
            trigger_value = '/fasten_mood'
            data = db.get_key_values('f_duration')

            weekdays = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun'}
            for row in data:
                user_id = row[1]
                chat_id = row[2]
                created_at = row[5]
                trigger_specific = created_at

                # check if the trigger is relevant for today or whether it has already been created
                created_at_day = created_at.date()
                today = datetime.datetime.now().date()

                ## create trigger for day1
                start_time = created_at
                # unique for _time values
                if start_time.hour+1 < 20:
                    trigger_time = (str(start_time.hour+1) + '-' + str(20) + '/2')
                    trigger_day = weekdays[datetime.datetime.now().weekday()]
                    if created_at_day == today and db.check_triggers(user_id, chat_id, trigger_value, trigger_day, trigger_time) == 0:
                        db.add_trigger(user_id, chat_id, trigger_value, trigger_time, trigger_day, trigger_specific, created_at)
                        print('trigger for fast: day1 added')

                ## create trigger for day2
                end_time = start_time + datetime.timedelta(hours=int(row[4]))
                # get weekday
                if start_time.day == end_time.day:
                    # add success message
                    if created_at_day == today and db.check_triggers(user_id, chat_id, trigger_value, trigger_day, trigger_time) == 0:
                        db.add_trigger(user_id, chat_id, '/fasten_success', end_time.strftime('%H:%M'), trigger_day, None, created_at)
                        print('trigger for fast: success added')
                else:
                    weekday = datetime.datetime.now().weekday()
                    if weekday < 6:
                        trigger_day = weekdays[datetime.datetime.now().weekday()+1]
                    else:
                        trigger_day = weekdays[0]
                    if end_time.hour+1 > 8:
                        trigger_time = (str(9) + '-' + str(min(end_time.hour, 20)) + '/2')
                        # add trigger for day 2
                        if created_at_day == today and db.check_triggers(user_id, chat_id, trigger_value, trigger_day, trigger_time) == 0:
                            db.add_trigger(user_id, chat_id, trigger_value, trigger_time, trigger_day, trigger_specific, created_at)
                            # add success message
                            db.add_trigger(user_id, chat_id, '/fasten_success', end_time.strftime('%H:%M'), trigger_day, None, created_at)
                            print('trigger for fast: day2 and success added')

    def remove_triggers(self):
        two_days_ago = datetime.date.today() - datetime.timedelta(days=2)
        triggers = db.get_trigger_values()
        check_in_cacher = []
        summary_cacher = []
        weight_cacher = []
        cache = {}
        for trigger in triggers:
            user_id = trigger[0]
            trigger_value = trigger[2]
            trigger_day = trigger[4]
            created_at = trigger[6]
            # remove completed fasten triggers
            if trigger_value in ["/fasten_mood", "/fasten_success"]:
                if created_at.date() < two_days_ago:
                    db.delete_from_triggers(user_id, trigger_value, trigger_day, created_at)
                    print('removed trigger')
            # remove check_ins that have been replaced by new ones
            elif trigger_value in ["/check_in"]:
                if user_id not in check_in_cacher:
                    check_in_cacher.append(user_id)
                    cache[user_id, trigger_value, 'created_at'] = created_at
                    cache[user_id, trigger_value, 'trigger_day'] = trigger_day
                # if there are several trigger_days (e.g. manual triggers)
                elif trigger_day != cache[user_id, trigger_value, 'trigger_day']:
                    cache[user_id, trigger_value, 'created_at'] = created_at
                    cache[user_id, trigger_value, 'trigger_day'] = trigger_day
                elif created_at > cache[user_id, trigger_value, 'created_at'] and trigger_day == cache[user_id, trigger_value, 'trigger_day']:
                    try:
                        db.delete_from_triggers(user_id, trigger_value, cache[user_id, trigger_value, 'trigger_day'], cache[user_id, trigger_value, 'created_at'])
                        print('removed trigger')
                    except Exception as e:
                        print(e)
                    cache[user_id, trigger_value, 'created_at'] = created_at
                elif created_at < cache[user_id, trigger_value, 'created_at'] and trigger_day == cache[user_id, trigger_value, 'trigger_day']:
                    try:
                        db.delete_from_triggers(user_id, trigger_value, trigger_day, created_at)
                        print('removed trigger')
                    except Exception as e:
                        print(e)
            # remove summaries that have been replaced by new ones
            elif trigger_value in ["/summary"]:
                if user_id not in summary_cacher:
                    summary_cacher.append(user_id)
                    cache[user_id, trigger_value, 'created_at'] = created_at
                    cache[user_id, trigger_value, 'trigger_day'] = trigger_day
                # if there are several trigger_days (e.g. manual triggers)
                elif trigger_day != cache[user_id, trigger_value, 'trigger_day']:
                    cache[user_id, trigger_value, 'created_at'] = created_at
                    cache[user_id, trigger_value, 'trigger_day'] = trigger_day
                elif created_at > cache[user_id, trigger_value, 'created_at'] and trigger_day == cache[user_id, trigger_value, 'trigger_day']:
                    try:
                        db.delete_from_triggers(user_id, trigger_value, cache[user_id, trigger_value, 'trigger_day'], cache[user_id, trigger_value, 'created_at'])
                        print('removed trigger')
                    except Exception as e:
                        print(e)
                    cache[user_id, trigger_value, 'created_at'] = created_at
                elif created_at < cache[user_id, trigger_value, 'created_at'] and trigger_day == cache[user_id, trigger_value, 'trigger_day']:
                    try:
                        db.delete_from_triggers(user_id, trigger_value, trigger_day, created_at)
                        print('removed trigger')
                    except Exception as e:
                        print(e)
            # remove wiegens that have been replaced by new ones
            elif trigger_value in ["/wiegen"]:
                # account for the fact that users can have up to 2 wiegen triggers
                if trigger_day == ['mon-fri']:
                    trigger_value = 'wiegen_wrkday'
                elif trigger_day == ['mon-fri']:
                    trigger_value = 'wiegen_wknd'

                if user_id not in weight_cacher:
                    weight_cacher.append(user_id)
                    cache[user_id, trigger_value, 'created_at'] = created_at
                    cache[user_id, trigger_value, 'trigger_day'] = trigger_day
                # if there are several trigger_days (e.g. manual triggers)
                elif trigger_day != cache[user_id, trigger_value, 'trigger_day']:
                    cache[user_id, trigger_value, 'created_at'] = created_at
                    cache[user_id, trigger_value, 'trigger_day'] = trigger_day
                elif created_at > cache[user_id, trigger_value, 'created_at'] and trigger_day == cache[user_id, trigger_value, 'trigger_day']:
                    try:
                        db.delete_from_triggers(user_id, '/wiegen', cache[user_id, trigger_value, 'trigger_day'], cache[user_id, trigger_value, 'created_at'])
                        print('removed trigger')
                    except Exception as e:
                        print(e)
                    cache[user_id, trigger_value, 'created_at'] = created_at
                elif created_at < cache[user_id, trigger_value, 'created_at'] and trigger_day == cache[user_id, trigger_value, 'trigger_day']:
                    try:
                        db.delete_from_triggers(user_id, '/wiegen', trigger_day, created_at)
                        print('removed trigger')
                    except Exception as e:
                        print(e)

    ## file retrieval
    def get_url(self, url):
        response = requests.get(url)
        content = response.content.decode("utf8")
        return content

    def get_json_from_url(self, url):
        import json
        content = DataBot.get_url(url)
        js = json.loads(content)
        return js

    def add_files_from_updates(self):
        file_data = db.get_files()
        for row in file_data:
            file_id = row[2].split("photo: ")[1]
            telegram_id = row[0]
            chat_id = row[1]
            key_value = row[3]
            intent = row[4]
            created_at = row[5]


            url = "https://api.telegram.org/bot{}/getFile?file_id={}".format(config.TELEGRAM_TOKEN, file_id)
            url_response = DataBot.get_json_from_url(url)

            file_path = url_response['result']['file_path']
            file = "{}_{}_{}_{}_{}-{}-{}".format(telegram_id, intent.replace("/", ""), key_value, created_at.date(), created_at.hour, created_at.minute, created_at.second)
            urllib.request.urlretrieve("https://api.telegram.org/file/bot{}/{}".format(config.TELEGRAM_TOKEN, file_path), "{}/user_files/{}".format(config.FILE_DIRECTORY, file))
            if db.check_files(telegram_id, intent, key_value, file) == 0:
                db.add_file(telegram_id, chat_id, intent, key_value, file, created_at)
                print('added file')

    def update_challenges(self):
        data = db.get_running_challenges()
        yesterday = datetime.datetime.now().date() - datetime.timedelta(days=1)
        completed_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for num, row in enumerate(data):
            if data[0][3].date() < yesterday:
                db.update_user_progress(completed_at, data[0][0], data[0][2])
                print('completed challenge')


if __name__ == '__main__':
    DataBot = DataBot()
    DataBot.find_key_values()
    DataBot.add_trigger_for_fast('f_duration')
    DataBot.add_trigger_for_times('wi_time')
    DataBot.add_trigger_for_times('wi_time_wrkday')
    DataBot.add_trigger_for_times('wi_time_wknd')
    DataBot.add_trigger_for_times('ci_time')
    DataBot.remove_triggers()
    DataBot.add_files_from_updates()
    DataBot.update_challenges()
