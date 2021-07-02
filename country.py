# -*- coding: utf-8 -*-
"""
Created on Tue Feb 16 17:36:06 2021

@author: lucas
"""

from pathlib import Path
from posixpath import join
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from countryinfo import CountryInfo
from data import global_case_data, global_fatality_data
plt.style.use('seaborn')


class Country(object):

    def __init__(self, name, window=7):
        # TODO: Allow custom label for country name (i.e. abbreviations) - put it in as plot label
        # TODO: Need to allow for different time windows
        self.name = name
        self.population = CountryInfo(name).population()

        self.window = window

        self.load_all()

        self.first_record, self.last_record = self.cases_series.index[[0, -1]]


    def load_all(self):
        # Load cases
        self._load_case_data()
        self._load_death_data()
        self._load_mortality_rate()


    def _load_case_data(self):

        self.cases_series = global_case_data().loc[self.name]
        self.cases_series.index = pd.to_datetime(self.cases_series.index)
        self.cases = self.cases_series.iloc[-1]
        self.cases_per_day = diff(self.cases_series, self.window)


    def _load_death_data(self):

        self.fatalities_series = global_fatality_data().loc[self.name]
        self.fatalities_series.index = pd.to_datetime(self.fatalities_series.index)
        self.fatalities = self.fatalities_series.iloc[-1]
        self.fatalities_per_day = diff(self.fatalities_series, self.window)


    def _load_mortality_rate(self):
        """ Calculate case fatality as a function of confirmed cases
        and fatality time series data."""
        self.case_fatality_series = self.fatalities_series.divide(self.cases_series)
        self.case_fatality = self.case_fatality_series.iloc[-1]

    def dailycaseplot(self, per_capita=False, ax=None, label=None):
        if label is None:
            label = self.name
        raw_data = self.cases_series
        daily_average = self.cases_per_day
        ylabel = 'Cases per Day'
        if per_capita:
            raw_data = normalize(raw_data, self.population)
            daily_average = normalize(daily_average, self.population)
            ylabel = 'Daily Cases per Million Residents'

        plot_series(raw_data, daily_average, label, ylabel, ax)

    def dailyfatalityplot(self, per_capita=False, ax=None, label=None):
        if label is None:
            label = self.name
        raw_data = self.fatalities_series
        daily_average = self.fatalities_per_day
        ylabel = 'Fatalities per Day'
        if per_capita:
            raw_data = normalize(raw_data, self.population)
            daily_average = normalize(daily_average, self.population)
            ylabel = 'Daily Deaths per Million Residents'

        plot_series(raw_data, daily_average, label, ylabel, ax)



def normalize(series, population):
    return series.divide(population).apply(lambda x: x*1000000)


def diff(df, window):
    """ Daily difference of cumulative data. Series is returned as rolling
    average with smoothing window defined by window argument.
    """
    return df.diff().rolling(window=window).mean()


def plot_series(raw_data, rolling_average, label, ylabel, ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(12,5))

    ax.bar(raw_data.diff().index, raw_data.diff(), width=1,
           color='black', alpha=0.25)
    ax.plot(rolling_average, linewidth=3, c='black')
    ax.set_ylabel(ylabel)
    ax.set_title('{}\n{}'.format(label, ylabel))
    formatplot(ax)
    fig.tight_layout()



def formatplot(ax):
    ax.spines['right'].set_color((.8,.8,.8))
    ax.spines['top'].set_color((.8,.8,.8))
    ax.set_ylim(bottom=0)
    ax.locator_params(axis='y', nbins=4)
    ax.grid('on', which='both', axis='y')