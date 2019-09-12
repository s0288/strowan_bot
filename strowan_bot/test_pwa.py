import unittest

import pandas as pd
import numpy as np
import config
import os

import urllib.request
from datetime import datetime, timedelta

class TestPWA(unittest.TestCase):
    def test_pwa(self):
        pwa_today = urllib.request.urlopen(f"https://strowan-flask.herokuapp.com/?id={config.TEST_USER}").getcode()
        pwa_yesterday = urllib.request.urlopen(f"https://strowan-flask.herokuapp.com/?id={config.TEST_USER}&date={datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')}").getcode()

        self.assertEqual(pwa_today, 200)
        self.assertEqual(pwa_yesterday, 200)


    def test_food_img(self):
        food_img_today = urllib.request.urlopen(f"https://s0288.pythonanywhere.com/static/strowan/pwa/2019/W{datetime.now().isocalendar()[1]}/food_imgs_{config.TEST_USER}_{datetime.strftime(datetime.now() - timedelta(0), '%Y-%m-%d')}.png").getcode()
        food_img_yesterday = urllib.request.urlopen(f"https://s0288.pythonanywhere.com/static/strowan/pwa/2019/W{datetime.now().isocalendar()[1]}/food_imgs_{config.TEST_USER}_{datetime.strftime(datetime.now() - timedelta(0), '%Y-%m-%d')}.png").getcode()

        self.assertEqual(food_img_today, 200)
        self.assertEqual(food_img_yesterday, 200)        
    

    def test_fasting_img(self):
        fasting_img_thisweek = urllib.request.urlopen(f"https://s0288.pythonanywhere.com/static/strowan/pwa/2019/W{datetime.now().isocalendar()[1]}/fasting_{config.TEST_USER}_W{datetime.now().isocalendar()[1]}.png").getcode()
        fasting_img_lastweek = urllib.request.urlopen(f"https://s0288.pythonanywhere.com/static/strowan/pwa/2019/W{(datetime.now() - timedelta(7)).isocalendar()[1]}/fasting_{config.TEST_USER}_W{(datetime.now() - timedelta(7)).isocalendar()[1]}.png").getcode()
        
        self.assertEqual(fasting_img_thisweek, 200)
        self.assertEqual(fasting_img_lastweek, 200)        


    def test_bokeh_plots(self):
        weight_plot = urllib.request.urlopen(f"https://s0288.pythonanywhere.com/static/strowan/pwa/2019/W{datetime.now().isocalendar()[1]}/weight_{config.TEST_USER}_{datetime.strftime(datetime.now() - timedelta(0), '%Y-%m-%d')}.html").getcode()
        ketone_plot = urllib.request.urlopen(f"https://s0288.pythonanywhere.com/static/strowan/pwa/2019/W{datetime.now().isocalendar()[1]}/ketone_{config.TEST_USER}_{datetime.strftime(datetime.now() - timedelta(0), '%Y-%m-%d')}.html").getcode()

        self.assertEqual(weight_plot, 200)
        self.assertEqual(ketone_plot, 200)        