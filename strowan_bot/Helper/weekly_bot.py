#!/usr/bin/python3.6
# coding: utf8
import logging

# read user data
import pandas as pd

# prepare and run papermill code
import datetime
import papermill as pm
import os

import sys #required because files in other folder
sys.path.append('../Handler/')
from db_bot import DBBot

DBBot = DBBot()

# don't run at night - only run between 4 and 8pm (might be different because it doesn't take CET)
if datetime.datetime.now().hour >= 4 or datetime.datetime.now().hour < 21:
    # get active users
    active_users = DBBot.get_active_users()

    # set current work week
    current_year = datetime.datetime.now().strftime("%y")
    current_work_week = datetime.datetime.now().strftime("%V")

    for row in active_users:
        platform_user_id = row[1]
        year = row[3].year
        month = row[3].month
        day = row[3].day

        # create jupyter notebook for user & week
        try:
            print('creating jupyter notebook for {}'.format(row['platform_user_id']))
            output_ipynb = '../../../nad_app/static/reports/' + str(platform_user_id) + "_" + current_year + current_work_week +'.ipynb'
            os.system(f"jupyter trust {output_ipynb}")
            pm.execute_notebook('../../../papermill.ipynb', output_ipynb, parameters = dict(user=platform_user_id, start_year=year, start_month=month, start_day=day))

        except Exception as e:
            print('error creating notebook for user {} ({})'.format(platform_user_id, platform_user_id))
            logging.exception("Exception in weekly_bot.py")
        # download html file without input code from jupyter notebook for user & week
        try:
            print('converting jupyter notebook to html...')
            ## add /home/s0288/.virtualenvs/my-virtualenv/bin/ to specify directory of virtual env for subprocess - reverts to default python 2.7 otherwise!
            nbconverttohtml_nocode ="/home/s0288/.virtualenvs/my-virtualenv/bin/jupyter nbconvert --ExecutePreprocessor.kernel_name=python3.6 --template=nbextensions --to=html ../../../nad_app/static/reports/" + str(platform_user_id) + "_" + current_year + current_work_week + ""
            os.system(nbconverttohtml_nocode)
            # remove the original jupyter file to save space
            print('removing jupyter notebook...')
            os.remove('../../../nad_app/static/reports/' + str(platform_user_id) + "_" + current_year + current_work_week + '.ipynb' + "")
        except Exception as e:
            print('error creating html file for user {} ({})'.format(platform_user_id, platform_user_id))
            logging.exception("Exception in weekly_bot.py")
