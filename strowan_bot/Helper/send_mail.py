import pandas as pd
import smtplib
from analytics import track_activity

import sys #required because files in parent folder
sys.path.append('../')
import config

import datetime
current_day = datetime.datetime.today().isocalendar()[2]
current_weeknr = datetime.datetime.today().isocalendar()[1]

# print all cols in df
pd.set_option('display.max_colwidth', -1)

# only send on Sunday
if current_day == 7:
    # get activity values
    periods = [1, 4, 12]
    activity_txt = track_activity(periods)

    # send email
    server = smtplib.SMTP_SSL('smtpout.EUROPE.secureserver.net', 465)
    server.login(config.ADMIN_MAIL, config.ADMIN_MAIL_PW)
    fromaddr = config.ADMIN_MAIL
    toaddr = config.TARGET_MAIL
    subject = f'Activity - W{current_weeknr}'
    msg = (f"From: {fromaddr}\r\nTo: {toaddr}\r\nSubject: {subject}\r\n\r\n{activity_txt}")
    server.sendmail(fromaddr, toaddr, msg)
    server.quit() 