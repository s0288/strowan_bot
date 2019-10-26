import smtplib
from analytics import track_activity

import sys #required because files in parent folder
sys.path.append('../')
import config

# get activity values
periods = [1, 4, 12]
activity_txt = track_activity(periods)

# send email
server = smtplib.SMTP_SSL('smtpout.EUROPE.secureserver.net', 465)
server.login(config.ADMIN_MAIL, config.ADMIN_MAIL_PW)
fromaddr = config.ADMIN_MAIL
toaddr = config.TARGET_MAIL
msg = (f"From: {fromaddr}\r\nTo: {toaddr}\r\n\r\n{activity_txt}")
server.sendmail(fromaddr, toaddr, msg)
server.quit() 