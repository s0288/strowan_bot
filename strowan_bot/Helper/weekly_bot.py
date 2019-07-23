#!/usr/bin/python3.6
# coding: utf8
import logging

# read user data
import pandas as pd

# prepare and run papermill code
import datetime
import papermill as pm
import os

from db_bot import DBBot

DBBot = DBBot()

# get active users
active_users = DBBot.get_active_users()

# set current work week
current_year = datetime.datetime.now().strftime("%y")
current_work_week = datetime.datetime.now().strftime("%V")

for row in active_users:
    platform_user_id = row[0]
    year = row[2].year
    month = row[2].month
    day = row[2].day

    # create jupyter notebook for user & week
    try:
        print('creating jupyter notebook for {}'.format(row['platform_user_id']))
        pm.execute_notebook('../../../papermill.ipynb', '../../../nad_app/static/reports/' + str(platform_user_id) + "_" + current_year + current_work_week +'.ipynb', parameters = dict(user=platform_user_id, start_year=year, start_month=month, start_day=day))
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
