import locale
locale.setlocale(locale.LC_TIME, "de_DE")
import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import matplotlib.image as mpimg

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

def get_output_location(user_id, plot_type='fast_overview'):
    curr_date = datetime.datetime.now().strftime("%y-%m-%d")
    curr_year = datetime.datetime.now().isocalendar()[0]
    curr_week = datetime.datetime.now().isocalendar()[1]

    # check if the user already has a folder. If not, create it
    file_path_users = f"{config.FILE_DIRECTORY}/static/users"
    file_path_users_user = f"{file_path_users}/{user_id}"
    file_path_users_user_week = f"{file_path_users_user}/{curr_year}_{curr_week}"
    file_path_users_user_week_fasts = f"{file_path_users_user_week}/fasts"
    if os.path.isdir(file_path_users) is False:
        os.mkdir(file_path_users)
    if os.path.isdir(file_path_users_user) is False:
        os.mkdir(file_path_users_user)
    if os.path.isdir(file_path_users_user_week) is False:
        os.mkdir(file_path_users_user_week)
    if os.path.isdir(file_path_users_user_week_fasts) is False:
        os.mkdir(file_path_users_user_week_fasts)   

    # define output file location for user
    output_file_location = f"{file_path_users_user_week_fasts}/{plot_type}_{curr_date}.png"

    return output_file_location

# get data on fasts from user
def get_fasting_data(user_id):
    #### get fasting-related values and clean df
    txt = f"""
            SELECT 
                u.created_at 
                , key_value
            FROM updates u
            WHERE 
                -- get bot messages for first interactions
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
        
    else:
        df_fast = None
    return df_fast


# plot recent fasts from user
def create_overview(df_fast, output_file_location=config.FILE_DIRECTORY):
    # if user hasn't fasted yet
    if df_fast is None:
        # plot bar chart
        fig, ax = plt.subplots()
        width = 0.5       # the width of the bars: can also be len(x) sequence
        ax.bar([], [], width)

        ax.set_ylabel('Stunden')
        ax.set_xlabel('Tage')
        ax.set_title('Aktuelle Fastenzeiten')
    # if user has existing fasting data
    else:
        ###### create plot
        # get values for recent fasts
        df_plot = df_fast.tail(7)
        fasts = df_plot.tail().created_at_abbr.values.tolist()
        durations = df_plot.tail().duration.values.tolist()
        labels_durations = df_plot.tail().duration_abbr.values.tolist()

        ###### save as png
        # get values for recent fasts
        df_plot = df_fast.tail(7)
        fasts = df_plot.created_at_abbr.values.tolist()
        durations = df_plot.duration.values.tolist()
        labels_durations = df_plot.duration_abbr.values.tolist()

        # plot bar chart
        fig, ax = plt.subplots()
        width = 0.5       # the width of the bars: can also be len(x) sequence
        ax.bar(fasts, durations, width)

        ax.set_ylabel('Stunden')
        ax.set_ylim([0,max(durations)+5])
        ax.set_xlabel('Tage')
        ax.set_title('Aktuelle Fastenzeiten', fontsize=16)

        # add durations as labels 
        rects = ax.patches
        for rect, label in zip(rects, labels_durations):
            height = rect.get_height()
            ax.text(rect.get_x() + rect.get_width() / 2, height + 0.5, label,
                    ha='center', va='bottom')


        ## add fast stats to plot
        # fix x axis to make sure text is properly aligned
        ax.set_xlim([-0.5, 6.5])
        # get coordinates of ylim to set text at proper height
        y0, ymax = plt.ylim()
        data_height = ymax - y0
        # add total fasting hours to plot
        total_duration = df_fast.duration.sum()
        plt.text(0, y0 + data_height * 1.3, f'Stunden gefastet:', fontsize=16)
        plt.text(0.8, y0 + data_height * 1.2, f'{total_duration:.0f}', fontsize=24)
        # add total fasting hours to plot
        count_fasts = df_fast.duration.count()
        plt.text(4.5, y0 + data_height * 1.3, f'Fastentrips:', fontsize=16)
        plt.text(5.1, y0 + data_height * 1.2, f'{count_fasts:.0f}', fontsize=24)

    plt.savefig(output_file_location, bbox_inches='tight')



############################################
### create progress plot
def create_progress_plot(total_duration, count_fasts, output_file_location=config.FILE_DIRECTORY):
    # <100 h: ameise
    # 100-200 h: katze
    # 200-500 h: kranich
    # 500-1000 h: fuchs
    # >1000 h: zen

    batch_threshold = [0, 100, 200, 500, 1000]
    batch = [{'name': 'Ameise', 'img': 'ant', 'coord_x': 165}, {'name': 'Fuchs', 'img': 'fox', 'coord_x': 180}, {'name': 'Katze', 'img': 'cat', 'coord_x': 180}, {'name': 'Kranich', 'img': 'crane', 'coord_x': 170}, {'name': 'Zen', 'img': 'zen', 'coord_x': 185}]

    # get first threshold that is not surpassed yet
    batch_value = np.array(batch_threshold)[batch_threshold <= total_duration][-1]
    batch_index = batch_threshold.index(batch_value)

    # get distance to next batch
    try:
        batch_next = np.array(batch_threshold)[batch_threshold > total_duration][0]
        diff_to_batch = batch_next - total_duration
    except:
        batch_next = None
        diff_to_batch = None

    # get batch
    img = mpimg.imread(f"{config.BATCH_DIRECTORY}/{batch[batch_index]['img']}.png")
    plt.imshow(img)
    plt.axis('off')

    # add name of batch and diff to next
    plt.text(batch[batch_index]["coord_x"], 200, f"{batch[batch_index]['name']}", fontsize=24)
    if diff_to_batch:
        plt.text(110, 215, f"Nächste Stufe in: {diff_to_batch:,.0f} Stunden", fontsize=16)

    # add total fasting hours to plot
    plt.text(65, 245, f'Stunden gefastet:', fontsize=16)
    plt.text(100, 270, f'{total_duration:.0f}', fontsize=24)

    # add total fasting count to plot
    plt.text(240, 245, f'Fastentrips:', fontsize=16)
    plt.text(275, 270, f'{count_fasts:.0f}', fontsize=24)

    plt.savefig(output_file_location, bbox_inches='tight')







if __name__ == '__main__':
    # get active users
    data = DBBot.get_active_users()
    ids = []
    for num, id in enumerate(data):
        ids.append(data[num][0])


    for user_id in ids:
        print(user_id)
        #### create fast_overview
        # check if path already exists, if not, create it
        output_file_location = get_output_location(user_id)
        # create fasting overviews for active users
        df_fast = get_fasting_data(user_id)
        create_overview(df_fast, output_file_location)

        #### create progress
        # get inputs for create_batch_plot
        total_duration = df_fast.duration.sum()
        count_fasts = df_fast.duration.count()
        output_file_location = get_output_location(user_id, plot_type='progress')
        # create batch plot
        create_progress_plot(total_duration, count_fasts, output_file_location)