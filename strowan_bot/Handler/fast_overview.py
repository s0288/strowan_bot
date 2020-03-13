import locale
locale.setlocale(locale.LC_TIME, "de_DE")
import datetime

import numpy as np
import pandas as pd

from bokeh.io import output_file, output_notebook, show
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.models import CategoricalTicker

import datetime
import os

from db_bot import DBBot
DBBot = DBBot()

import sys #required because files in parent folder
sys.path.append('..')
import config
from sqlalchemy import *
engine = create_engine(config.POSTGRES)
metadata = MetaData(engine)
conn = engine.connect()


def create_overview(user_id, output_file_bokeh=config.BASE_DIRECTORY):
    #### get fasting-related values and clean df
    txt = f"""
            SELECT 
                u.created_at 
                , key_value
            FROM updates u
            WHERE 
                u.platform_chat_id = {user_id} AND u.platform_user_id != {user_id} 
                AND u.key_value in ('fast_start_text', 'fasten_end_text')
            ORDER BY u.id ASC 
            """
    data = pd.read_sql_query(txt, conn)

    # only continue if user has started a fast yet:
    if len(data) > 0:
        ## remove duplicate button clicks in-between beginning and end of fast
        # create new data frame for the cleaned rows
        df_fast = pd.DataFrame(columns=['created_at', 'key_value'])

        # key values
        fasten_start = 'fast_start_text'
        fasten_end = 'fasten_end_text'

        # loop over data - Is there a vectorised way to do this?
        fast_started = 0
        for i in data.iterrows():
            # check if user started fast but ignore second starts without ends
            if fast_started == 0:
                if i[1].key_value == fasten_start:
                    df_fast.loc[len(df_fast)] = i[1]
                    fast_started = 1
            # check if user ended fast after he started it
            if fast_started == 1:
                if i[1].key_value == fasten_end:
                    df_fast.loc[len(df_fast)] = i[1]
                    fast_started = 0

        # if last row is fast_start add fast_ongoing
        if df_fast.key_value.iloc[[-1]].values[0] == 'fast_start_text':
            df_fast.loc[len(df_fast)] = [datetime.datetime.now().replace(microsecond=0), 'fast_ongoing']            

        # calculate duration of each fast in hours
        df_fast["duration"] = (df_fast['created_at'].shift(-1)-df_fast['created_at']) / np.timedelta64(1, 'h')

        # only keep the starting values
        df_fast = df_fast.loc[df_fast.key_value == 'fast_start_text']

        # only keep fast with longest duration on same date -- ALTERNATIVE FROM ZERO: Sum all fasts on a given day
        df_fast["created_at_date"] = df_fast.created_at.dt.date
        idx = df_fast.groupby('created_at_date').duration.transform(max) == df_fast.duration
        df_fast = df_fast[idx].reset_index(drop=True)

        # create abbreviated date values
        df_fast["created_at_abbr"] = df_fast.created_at.dt.strftime('%d. %b')
        # create abbreviated duration values
        df_fast["duration_abbr"] = df_fast.duration.round().astype(int).astype(str) + " h"


        ##### create bokeh plot

        # get values for recent fasts
        df_plot = df_fast.tail(7)
        fasts = df_plot.tail().created_at_abbr.values.tolist()
        durations = df_plot.tail().duration.values.tolist()
        labels_durations = df_plot.tail().duration_abbr.values.tolist()

        # create plot
        p = figure(x_range=fasts, y_range=(0, max(durations)+5), plot_height=250, title="Aktuelle Fastenzeiten",
                toolbar_location=None, tools="")
        p.vbar(x=fasts, top=durations, width=0.5)

        # add fasting hours as labels
        source = ColumnDataSource(dict(x=fasts, y=durations, text=labels_durations))
        labels = LabelSet(x='x', y='y', text='text', level='glyph',
                x_offset=-10, y_offset=10, source=source, render_mode='css')
        p.add_layout(labels)

        # remove axes grid lines
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None

        # specify output
        output_file(output_file_bokeh)

        show(p)


# get active users
data = DBBot.get_active_users()
ids = []
for num, id in enumerate(data):
    ids.append(data[num][0])


curr_date = datetime.datetime.now().strftime("%y-%m-%d")

for user_id in ids:
    
    # check if the user already has a folder. If not, create it
    file_path_users = f"{config.BASE_DIRECTORY}/users"
    file_path_users_user = f"{file_path_users}/{user_id}"
    file_path_users_user_fasts = f"{file_path_users_user}/fasts"
    if os.path.isdir(file_path_users) is False:
        os.mkdir(file_path_users)
    if os.path.isdir(file_path_users_user) is False:
        os.mkdir(file_path_users_user)
    if os.path.isdir(file_path_users_user_fasts) is False:
        os.mkdir(file_path_users_user_fasts)
    
    # define output file location for user
    output_file_bokeh = f"{file_path_users_user_fasts}/fast_overview_{curr_date}.html"
    
    # create fasting overviews for active users
    create_overview(user_id, output_file_bokeh)