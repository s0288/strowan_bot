#!/usr/bin/python3.6
# coding: utf8
import logging
import requests
import json
import os
import urllib
import datetime
import re

from db_bot import DBBot

import sys #required because files in parent folder
sys.path.append('../')
import config

DBBot = DBBot()

class DataBot:

    def find_key_values(self):
        # get key values
        last_key_value = DBBot.get_last_value('key_values')
        # check if no files have been saved so far
        if last_key_value[0] == None:
            data = DBBot.get_values_from_updates('key_values')
        else:
           data = DBBot.get_values_from_updates('key_values', last_key_value[0].strftime('%Y-%m-%d %H:%M:%S'))
        data.reverse()
        for row in data:
            platform_user_id = row[0]
            platform_chat_id = row[1]
            key_value_value = row[2] # will be split up in if clauses
            key_value = row[3]
            created_at = row[5]
            is_bot = row[6]
            received_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 'value' and 'duration' are deprecated
            if "_float" in key_value or "_integer" in key_value:
                if re.findall("\d+\.\d+", key_value_value):
                    key_value_value = re.findall("\d+\.\d+", key_value_value)[0]
                    DBBot.add_key_value(platform_user_id, platform_chat_id, key_value, key_value_value, created_at, received_at)
                    print('key_value for {} added'.format(key_value))
                elif re.findall("\d+\,\d+", key_value_value):
                    key_value_value = re.findall("\d+\,\d+", key_value_value)[0]
                    key_value_value = key_value_value.replace(',','.')
                    DBBot.add_key_value(platform_user_id, platform_chat_id, key_value, key_value_value, created_at, received_at)
                    print('key_value for {} added'.format(key_value))
                elif re.findall("\d+", key_value_value):
                    key_value_value = re.findall("\d+", key_value_value)[0]
                    DBBot.add_key_value(platform_user_id, platform_chat_id, key_value, key_value_value, created_at, received_at)
                    print('key_value for {} added'.format(key_value))
            # 'time' is deprecated
            elif "_time" in key_value and "_timestamp" not in key_value:
                if re.findall("\d+\:\d+", key_value_value):
                    key_value_value = re.findall("\d+\:\d+", key_value_value)[0]
                    DBBot.add_key_value(platform_user_id, platform_chat_id, key_value, key_value_value, created_at, received_at)
                    print('key_value for {} added'.format(key_value))
                elif re.findall("\d+\.\d+", key_value_value):
                    key_value_value = re.findall("\d+\.\d+", key_value_value)[0]
                    key_value_value = key_value_value.replace('.',':')
                    DBBot.add_key_value(platform_user_id, platform_chat_id, key_value, key_value_value, created_at, received_at)
                    print('key_value for {} added'.format(key_value))
                elif re.findall("\d+\,\d+", key_value_value):
                    key_value_value = re.findall("\d+\,\d+", key_value_value)[0]
                    key_value_value = key_value_value.replace(',',':')
                    DBBot.add_key_value(platform_user_id, platform_chat_id, key_value, key_value_value, created_at, received_at)
                    print('key_value for {} added'.format(key_value))
                elif re.findall("\d+", key_value_value):
                    key_value_value = re.findall("\d+", key_value_value)[0]
                    # add a leading zero and 2 zeros at the end
                    key_value_value = key_value_value + ':00'
                    DBBot.add_key_value(platform_user_id, platform_chat_id, key_value, key_value_value, created_at, received_at)
                    print('key_value for {} added'.format(key_value))
            # meal_entry, meal_path, meal_description, meal_reason are deprecated
            elif "user_photo" in key_value or "_text" in key_value:
                key_value_value = key_value_value
                DBBot.add_key_value(platform_user_id, platform_chat_id, key_value, key_value_value, created_at, received_at)
                print('key_value for {} added'.format(key_value))
            # currently missing: timestamp


    ## file retrieval
    def get_json_from_url(self, url):
        response = requests.get(url)
        content = response.content.decode("utf8")
        js = json.loads(content)
        return js

    def add_files_from_updates(self):
        # only read unretrieved files
        last_file = DBBot.get_last_value('files')
        # check if no files have been saved so far
        if last_file[0] == None:
            data = DBBot.get_values_from_updates('files')
        else:
            data = DBBot.get_values_from_updates('files', last_file[0].strftime('%Y-%m-%d %H:%M:%S'))
        data.reverse()
        try:
            for row in data:
                # retrieve new file from update
                platform_user_id = row[0]
                platform_chat_id = row[1]
                file_id = row[2].split("photo: ")[1]
                key_value = row[3]
                intent = row[4]
                created_at = row[5]
                received_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # get file location on Telegram server
                url = "https://api.telegram.org/bot{}/getFile?file_id={}".format(config.TELEGRAM_TOKEN, file_id)
                url_response = DataBot.get_json_from_url(url)

                # save file
                file_path = url_response['result']['file_path']
                file = "{}_{}_{}_{}_{}-{}-{}".format(platform_user_id, intent.replace("/", ""), key_value, created_at.date(), created_at.hour, created_at.minute, created_at.second)
                # get location of folder for file
                weeknr =  str(created_at.date().isocalendar()[0]) + '-' + str(created_at.date().isocalendar()[1])
                file_location = "{}/user_files/{}".format(config.FILE_DIRECTORY, weeknr)
                # check if folder (YYYY-WW) already exists, otherwise create it
                if not os.path.exists(file_location):
                    os.makedirs(file_location)
                urllib.request.urlretrieve("https://api.telegram.org/file/bot{}/{}".format(config.TELEGRAM_TOKEN, file_path), "{}/{}".format(file_location, file))
                print('retrieved file')
                DBBot.add_file(platform_user_id, platform_chat_id, intent, key_value, file, created_at, received_at)
                print('added file to db')
        except Exception as e:
            logging.exception("Error in add_files_from_updates")

    # trigger functions
    def add_trigger_for_times(self, key_value):
        if key_value == 'weight_notif_wknd_time' or key_value == 'weight_notif_work_time':
            trigger_value = '/wiegen'
            if key_value in ['wi_time_wknd', 'weight_notif_wknd_time']:
                trigger_day = "sat-sun"
            elif key_value in ['wi_time_wrkday', 'weight_notif_work_time']:
                trigger_day = "mon-fri"
        elif key_value == 'assessment_text':
            trigger_value = '/assessment'
            trigger_day = 'sun'
        # get msg specifics for key_value
        data = DBBot.get_key_values(key_value)
        for row in data:
            platform_user_id = row[1]
            platform_chat_id = row[2]
            created_at = row[5]
            # unique for _time values
            if "time" in key_value:
                trigger_time = row[4]
            else:
                trigger_time = '17:00'
            # set up trigger in db
            # check if already there or add
            if DBBot.check_triggers(platform_user_id, platform_chat_id, trigger_value, trigger_day, trigger_time) == 0:
                received_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                DBBot.add_trigger(platform_user_id, platform_chat_id, trigger_value, trigger_time, trigger_day, created_at, received_at)
                print('trigger for {} added'.format(trigger_value))
        

    # convert hourly fast to cronjob hours
    def add_trigger_for_fast(self, key_value):
        ## very inefficient as of now because it retrieves ALL fasting triggers, even the expired ones
        data = DBBot.get_key_values(key_value)

        weekdays = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun'}
        for row in data:
            created_at = row[5]
            created_at_day = created_at.date()
            today = datetime.datetime.now().date()
            fasting_duration = int(row[4])

            # check whether fasten key value is still active (within fasting window)
            if today - datetime.timedelta(hours=fasting_duration) < created_at_day:
                platform_user_id = row[1]
                platform_chat_id = row[2]
                # calculate end of fast
                end_time = created_at + datetime.timedelta(hours=fasting_duration)
                # how many days from today to end of fast?
                duration_days = (end_time - created_at).days

                for i in range(0,duration_days+1):
                    day_of_week = created_at.weekday()+i
                    # day_of_week can only take values between 0 and 6
                    if day_of_week > 6:
                        day_of_week = day_of_week - 7
                    trigger_day = weekdays[day_of_week]
                    if i == duration_days:
                        trigger_value = '/fasten_success'
                        trigger_time = end_time.time().strftime('%H:%M')
                    # currently also adds old fasting triggers. Better would be to only consider fasting key values from this week or sth
                    if DBBot.check_triggers(platform_user_id, platform_chat_id, trigger_value, trigger_day, trigger_time) == 0:
                        received_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        DBBot.add_trigger(platform_user_id, platform_chat_id, trigger_value, trigger_time, trigger_day, created_at, received_at)
                        print('trigger for fast: day {} of {} added'.format(i, duration_days))

    def remove_triggers(self, trigger_value):
        weekdays_reversed = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}
        data = DBBot.get_trigger_values(trigger_value=trigger_value)
        if data:
            # calculate today's date for later use
            today = datetime.datetime.now().date()
            for row in data:
                created_at = row[5]
                created_at_day_of_week = created_at.weekday()
                trigger_day = row[4]
                trigger_day_day_of_week = weekdays_reversed[trigger_day]
                if created_at_day_of_week > trigger_day_day_of_week:
                    trigger_day_day_of_week = trigger_day_day_of_week + 7
                days_since_creation = trigger_day_day_of_week - created_at_day_of_week
                date_of_trigger = (created_at + datetime.timedelta(days=days_since_creation)).date()

                # check if date of trigger is earlier than today. If so, delete it:
                if date_of_trigger < today:
                    user_id = row[0]
                    DBBot.delete_from_triggers(user_id, trigger_value, trigger_day, created_at)
                    print('removed trigger')

if __name__ == '__main__':
    DataBot = DataBot()
    DataBot.find_key_values()
    DataBot.add_files_from_updates()
    DataBot.add_trigger_for_times('weight_notif_work_time')
    DataBot.add_trigger_for_times('weight_notif_wknd_time')
    DataBot.add_trigger_for_times('assessment_text')
    DataBot.add_trigger_for_fast('f_duration')
    DBBot.delete_triggers_by_inactive_users()
    # fasten_progress is deprecated
    DataBot.remove_triggers('/fasten_progress')
    DataBot.remove_triggers('/fasten_success')
