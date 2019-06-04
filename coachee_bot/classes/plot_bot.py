import sys #required because files in other folder
sys.path.append('../')
import config

import sys #required because files in other folder
sys.path.append('../classes/')
from dbhelper import DBHelper

# somehow required for pythonanywhere
import matplotlib as mpl
mpl.use('Agg')

import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib.ticker as plticker
import numpy as np
import pandas as pd
import datetime
import math

db = DBHelper()

def roundtoclosestfloor(x, mod, base=3):
    if mod == 'floor':
        return int(base * math.floor(float(x)/base))
    elif mod == 'ceil':
        return int(base * math.ceil(float(x)/base))

def get_values_for_plot(key_value, chat_id):
    data = db.get_key_values(key_value, chat_id)
    if data:
        iterator = []
        xlabs = []
        xvalues = []
        yvalues = []
        if key_value == 'wi_value':
            start_time = data[-1][5].date()
            for num, row in enumerate(data):
                date = row[5].date()
                date_wo_year = row[5].date().strftime("%d.%m")
                if date not in iterator:
                    iterator.append(str(date))
                    xlabs.append(str(date_wo_year))
                    xvalues.append((date-start_time).days)
                    yvalues.append(float(row[4]))
            # order the values
            xlabs = list(reversed(xlabs))
            xvalues = list(reversed(xvalues))
            yvalues = list(reversed(yvalues))
            length_xaxis = len(yvalues)

        # for fasten mood, create a breakdown of the hours
        elif key_value == 'f_mood':
            for num, row in enumerate(data):
                date = row[5].date()
                today = datetime.date.today()
                yesterday = datetime.date.today() - datetime.timedelta(days=1)
                if date == today or date == yesterday:
                    hour = row[5].time().strftime("%H:00")
                    if hour not in iterator:
                        iterator.append(str(date))
                        xlabs.append(str(hour))
                        xvalues.append(num)
                        yvalues.append(float(row[4]))
            # order the values
            xlabs = list(reversed(xlabs))
            yvalues = list(reversed(yvalues))
            length_xaxis = len(yvalues)

        elif key_value == 'ci_mood':
            for num, row in enumerate(data):
                date = row[5].date()
                date_wo_year = row[5].date().strftime("%d.%m")
                if date not in iterator:
                    iterator.append(str(date))
                    xlabs.append(str(date_wo_year))
                    xvalues.append(num)
                    yvalues.append(float(row[4]))
            # order and only keep the last 7 values
            xlabs = list(xlabs)
            yvalues = list(yvalues)
            xlabs = xlabs[:7]
            xvalues = xvalues[:7]
            yvalues = yvalues[:7]
            xlabs = list(reversed(xlabs))
            xvalues = list(reversed(xvalues))
            yvalues = list(reversed(yvalues))
            length_xaxis = len(yvalues)
    # in case a user doesn't have values (shouldn't happen)
    else:
        xlabs = ['29.01', '30.01', '03.02', '04.02', '05.02', '06.02', '07.02', '08.02', '09.02', '10.02', '12.02', '13.02', '14.02', '14.02', '15.02', '16.02', '17.02', '18.02', '18.02', '18.02', '19.02', '20.02', '21.02', '22.02', '23.02']
        xvalues = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
        yvalues = [77.0, 76.3, 75.6, 75.2, 74.9, 74.7, 74.7, 74.9, 74.9, 74.9, 74.2, 74.2, 73.8, 73.8, 75.6, 74.6, 74.2, 74.2, 74.2, 74.2, 74.4, 73.7, 74.1, 74.1, 73.9]
        length_xaxis = len(yvalues)
    return xlabs, xvalues, yvalues, length_xaxis

def movingaverage(interval, window_size):
    window = np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'valid')

def create_ma(xvalues, yvalues, window_size):
    # calculate moving average with lag window_size
    ymav = movingaverage(yvalues, window_size)
    # throw out those values that cannot be used for lag
    xvalues = np.array(xvalues)
    yvalues = np.array(yvalues)
    plt.plot(xvalues[window_size-1:], ymav)

def create_plot(key_value, user_id, xvalues, yvalues, length_xaxis, xlabels=None, ylabels=None):
    date = datetime.datetime.now().date()
    # setting y axis labels
    fig, ax = plt.subplots()
    # set dates as xaxis labels
    from matplotlib.ticker import FuncFormatter, MaxNLocator
    def format_fn(tick_val, tick_pos):
        if int(tick_val) in xvalues:
            return xlabels[int(tick_val)]
        else:
            return ''
    ax.xaxis.set_major_formatter(FuncFormatter(format_fn))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    # make sure axis ticks are all shown
    ax.xaxis.get_major_locator().set_params(nbins=length_xaxis)
    # create plot and set achieved and achievable goal
    plt.plot(xvalues, yvalues)
    # define titles and intermediate goals
    if key_value == 'wi_value':
        xtitle = 'Datum'
        ytitle = 'Dein Gewicht (kg)'
        title = 'Dein Gewicht verändert sich'
        # intermediate goal lines
        plt.axhline(y=roundtoclosestfloor(min(yvalues), 'ceil'), color='b', linestyle='dashed')
        plt.axhline(y=roundtoclosestfloor(min(yvalues), 'ceil')-2, color='r', linestyle='dashed')
        # truncate x and y axis
        ax.set_ylim(ymax=max(yvalues) + 1)
        ax.set_ylim(ymin=min(yvalues) - 1)
        # this locator puts ticks at regular intervals - make sure that the max axis length is 8 and min 1
        loc = plticker.MultipleLocator(base=math.ceil(float(length_xaxis)/8))
        ax.xaxis.set_major_locator(loc)
    elif key_value == 'ci_mood':
        xtitle = 'Datum'
        ytitle = 'Deine Stimmung'
        title = 'So hast du dich gefühlt'
        # truncate x and y axis
        ax.set_ylim(ymin=1)
        # this locator puts ticks at regular intervals - make sure that the max num axis ticks is 8 and min 1
        loc = plticker.MultipleLocator(base=math.ceil(float(length_xaxis)/8))
        ax.xaxis.set_major_locator(loc)
    elif key_value == 'f_mood':
        xtitle = 'Uhrzeit'
        ytitle = 'Deine Stimmung'
        title = 'So hast du dich gefühlt'
        # truncate x and y axis
        ax.set_ylim(ymin=1)
    # y axis ticks move in integer steps
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    # rotate x axis ticks 45°
    plt.xticks(rotation=45)
    plt.title(title)
    plt.xlabel(xtitle)
    plt.ylabel(ytitle)
#    plt.show()
    fig.savefig('../../nad_app/static/plots/{}_{}_{}.png'.format(user_id, key_value, datetime.datetime.now().date()))
    plt.close()

def create_weight_plot(user_id, xvalues, yvalues, window_size, title):
    # calculate moving average with lag window_size
    if window_size == 0:
        plt.plot(xvalues, yvalues)
        plt.xlabel('Tage seit Start')
        plt.ylabel('Kilo')
        plt.title(title)
    else:
        ymav = pd.DataFrame(yvalues).rolling(window_size, min_periods=1).mean()
        ystd = pd.DataFrame(yvalues).rolling(window_size, min_periods=1).std()

        # create 2 axes
        fig, ax = plt.subplots()

        ax.plot(xvalues, yvalues, '.--', label='tagesaktuell')
        ax.plot(xvalues, ymav, color='red', label='Ø über 14 Tage')
        #ax.plot(xvalues, ymav+ystd, color='k')
        #ax.plot(xvalues, ymav-ystd, color='k')

        ax.set_xlabel('Tage seit Start')
        ax.legend(loc="upper right", borderaxespad=0.3)

        plt.title(title)
        fig.savefig('../../nad_app/static/plots/{}_{}_{}.png'.format(user_id, key_value, datetime.datetime.now().date()))
        plt.close()
        return ymav



# ich: 415604082
# Mama: 495346285
# Lui: 36718427
# Luis: 164570223
data = db.get_users()
ids = []
for num, id in enumerate(data):
    ids.append(data[num][0])

key_values = ["wi_value", "ci_mood", "f_mood"]
for key_value in key_values:
    for chat_id in ids:
        if key_value in ["ci_mood", "f_mood"]:
            try:
                xlabs, xvalues, yvalues, length_xaxis = get_values_for_plot(key_value, chat_id)
                create_plot(key_value, chat_id, xvalues, yvalues, length_xaxis, xlabs)
            except Exception as e:
                print(e)
                print(("no data for {} of {}").format(key_value, chat_id))
        elif key_value in ["wi_value"]:
            try:
                xlabs, xvalues, yvalues, length_xaxis = get_values_for_plot(key_value, chat_id)
                title = 'Deine Entwicklung - täglich und 14-Tagesdurchschnitt'
                ymav = create_weight_plot(chat_id, xvalues, yvalues, 14, title)
            except Exception as e:
                print(e)
                print(("no data for {} of {}").format(key_value, chat_id))
