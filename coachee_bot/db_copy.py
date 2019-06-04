import datetime
import shutil
shutil.copy('db_main.sqlite', './db_export/{}_db_main.sqlite'.format(datetime.datetime.now().strftime('%Y-%m-%d')))
