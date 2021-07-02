# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 17:38:46 2021

@author: lucas
"""

from posixpath import join
import pandas as pd


BASEURL = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data'
TIMESERIES = join(BASEURL, 'csse_covid_19_time_series')
DAILY_REPORT = join(BASEURL, 'csse_covid_19_daily_reports_us')


def load_global_url(url):
    df = pd.read_csv(url, index_col=1)
    df = df.drop(['Lat','Long', 'Province/State'], axis=1)
    df = df.groupby('Country/Region').sum()
    return df


def load_us_url(url):
    df = pd.read_csv(url, index_col=1)
    df['Name'] = df['Admin2'].str.cat(df['Province_State'],sep=", ")
    df = df.rename(columns={'Admin2': 'County'})
    df = df.set_index('Name', drop=True)
    return df


def global_case_data():
    url = join(TIMESERIES, 'time_series_covid19_confirmed_global.csv')
    df = load_global_url(url)
    return df


def global_fatality_data():
    url = join(TIMESERIES, 'time_series_covid19_deaths_global.csv')
    df = load_global_url(url)
    return df


def us_case_data():
    url = join(TIMESERIES, 'time_series_covid19_confirmed_US.csv')
    df = load_us_url(url)
    return df


def us_fatality_data():
    url = join(TIMESERIES, 'time_series_covid19_deaths_US.csv')
    df = load_us_url(url)
    return df

df = us_fatality_data()
