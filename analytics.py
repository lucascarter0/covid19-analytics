# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 10:16:52 2021

@author: lucas
"""

import pandas as pd
import matplotlib.pyplot as plt

from countryinfo import CountryInfo

import plots
from databases import JhuData
plt.style.use('seaborn')



class Container():
    def __init__(self, name, window=7):
        self.name = name
        self.window = window


    def _load(self, data):
        series = data.loc[self.name]
        series.index = pd.to_datetime(series.index)
        return series


    def _record(self, series, attrname):
        setattr(self, '{}_series'.format(attrname), series)
        setattr(self, 'total_{}'.format(attrname), series.iloc[-1])
        setattr(self, '{}_per_day'.format(attrname), diff(series, self.window))


    def get_params(self):
        self.load_fatality_rate()
        self.first_record, self.last_record = self.cases_series.index[[0, -1]]


    def load_fatality_rate(self):
        """ Calculate case fatality as a function of confirmed cases
        and fatality time series data."""
        self.case_fatality_series = self.fatalities_series.divide(self.cases_series)
        self.case_fatality = self.case_fatality_series.iloc[-1]


    def dailycaseplot(self, per_capita=False, gca=None, label=None):
        if label is None:
            label = self.name
        data = self.cases_series
        rolling_average = self.cases_per_day
        ylabel = 'Cases per Day'
        if per_capita:
            data = normalize(data, self.population)
            rolling_average = normalize(rolling_average, self.population)
            ylabel = 'Daily Cases per Million Residents'

        plots.plot_series(data, rolling_average, label, ylabel, gca)


    def dailyfatalityplot(self, per_capita=False, gca=None, label=None):
        if label is None:
            label = self.name
        data = self.fatalities_series
        rolling_average = self.fatalities_per_day
        ylabel = 'Fatalities per Day'
        if per_capita:
            data = normalize(data, self.population)
            rolling_average = normalize(rolling_average, self.population)
            ylabel = 'Daily Deaths per Million Residents'

        plots.plot_series(data, rolling_average, label, ylabel, gca)


    def dailyhospitalizationplot(self, per_capita=False, gca=None, label=None):
        if label is None:
            label = self.name
        data = self.hospitalizations_series
        rolling_average = self.hospitalizations_per_day
        ylabel = 'Hospitalizations per Day'
        if per_capita:
            data = normalize(data, self.population)
            rolling_average = normalize(rolling_average, self.population)
            ylabel = 'Daily Hospitalizations per Million Residents'

        plots.plot_series(data, rolling_average, label, ylabel, gca)



class Country(Container):

    def __init__(self, name, window=7):
        # TODO: Allow custom label for country name (i.e. abbreviations) - put it in as plot label
        # TODO: Need to allow for different time windows
        super().__init__(name, window)

        all_data = JhuData()
        self._record(self._load(all_data.global_cases()), 'cases')
        self._record(self._load(all_data.global_fatalities()), 'fatalities')

        self.population = CountryInfo(self.name).population()
        self.get_params()



class State(Container):

    def __init__(self, name, window=7):
        super().__init__(name, window)

        self.record_data()
        self.population = JhuData().us_population(groupby='state').loc[self.name]

        self.get_params()

    def record_data(self):
        all_data = pd.read_csv('https://raw.githubusercontent.com/lucascarter0/covid19-analytics/master/us_combined_covid_data.csv')
        all_data = all_data.set_index(['state', 'date'])
        self._record(self._load(all_data['total_cases']), 'cases')
        self._record(self._load(all_data['total_deaths']), 'fatalities')
        self._record(self._load(all_data['total_hospitalizations']), 'hospitalizations')
        self._record(self._load(all_data['series_complete_yes']), 'fully_vaccinated')
        self._record(self._load(all_data['administered_dose1_recip']), 'partial_plus_vaccinated')





class County(Container):

    def __init__(self, name, window=7):
        super().__init__(name, window)

        all_data = JhuData()
        data = all_data.us_cases()

        self._record(self.__load(data), 'cases')

        data = self.getpopulation(all_data.us_fatalities(groupby='county'))
        self._record(self.__load(data), 'fatalities')

        self.get_params()


    def __load(self, data):
        series = data.loc[self.name]
        for index in series.index:
            try:
                pd.to_datetime(index)
            except:
                setattr(self, index.lower(), series[index])
                series = series.drop(index, axis=0)
        series.index = pd.to_datetime(series.index)
        return series


    def getpopulation(self, data):
        if 'Population' in data.columns:
            self.population = data.loc[self.name, 'Population']
            data = data.drop('Population', axis=1)
        return data



def normalize(series, population, per=1000000):
    """ Return series as a proportion of population.

    Example:
        Fatalities per million residents.
        normalize(State.cases_per_day, per=1000000)
    """
    return series.divide(population).apply(lambda x: x*per)


def diff(series, window):
    """ Daily difference of cumulative data. Series is returned as rolling
    average with smoothing window defined by window argument.
    """
    return series.diff().rolling(window=window).mean()
