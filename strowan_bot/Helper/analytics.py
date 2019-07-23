#!/usr/bin/python3.6
# coding: utf8

# prepare and run papermill code
import datetime
import papermill as pm
import os

import sys #required because files in other folder
sys.path.append('../Handler/')
from db_bot import DBBot

DBBot = DBBot()

# set current work week
current_date = datetime.datetime.now().strftime("%Y-%m-%d")

# create ipynb
try:
    print('creating analytics notebook')
    pm.execute_notebook('../../../analytics.ipynb', '../../../nad_app/static/reports/analytics/analytics' + "_" + current_date +'.ipynb', parameters = dict())
except Exception as e:
    print('error creating analytics notebook')
    print(e)
# download html file
try:
    print('converting jupyter notebook to html...')
    ## add /home/s0288/.virtualenvs/my-virtualenv/bin/ to specify directory of virtual env for subprocess - reverts to default python 2.7 otherwise!
    nbconverttohtml_nocode ="/home/s0288/.virtualenvs/my-virtualenv/bin/jupyter nbconvert --ExecutePreprocessor.kernel_name=python3.6 --template=nbextensions --to=html ../../../nad_app/static/reports/analytics/analytics" + "_" + current_date + ""
    os.system(nbconverttohtml_nocode)
    # remove the original jupyter file to save space
    print('removing jupyter notebook...')
    os.remove('../../../nad_app/static/reports/analytics/analytics' + "_" + current_date + '.ipynb' + "")
except Exception as e:
    print('error creating html file')
    print(e)
