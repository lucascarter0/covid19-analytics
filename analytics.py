# -*- coding: utf-8 -*-


import pandas as pd
import numpy as np
from pathlib import Path
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
        self.calculate_fatality_rate()
        self.first_record, self.last_record = self.cases_series.index[[0, -1]]


    def calculate_fatality_rate(self):
        """ Calculate case fatality as a function of confirmed cases
        and fatality time series data."""
        self.case_fatality_series = self.fatalities_series.divide(self.cases_series)
        self.case_fatality = self.case_fatality_series.iloc[-1]


    def dailycaseplot(self, per_capita=False, gca=None, label=None):
        ''' Summary plot of confirmed cases per day. Plots bar plot of raw data
        behind a rolling average. Rolling average window and date range
        of data during class instantiation.
        
        Arguments:
            per_capita: Plot data per 100k residents
            gca: Existing matplotlib axes to plot two (optional)
            label: Custom label for data legend. Uses name attribute by default
        '''
        if label is None:
            label = self.name
        data = self.cases_series
        rolling_average = self.cases_per_day
        ylabel = 'Cases per Day'

        plotter = plots.DailyPlotter(gca, label, ylabel)
        plotter.summary_plot(data, rolling_average, per_capita, self.population)


    def dailyfatalityplot(self, per_capita=False, gca=None, label=None):
        ''' Summary plot of COVID-19 deaths per day. Plots bar plot of raw data
        behind a rolling average. Rolling average window and date range
        of data during class instantiation.
        
        Arguments:
            per_capita: Plot data per 100k residents
            gca: Existing matplotlib axes to plot two (optional)
            label: Custom label for data legend. Uses name attribute by default
        '''
        if label is None:
            label = self.name
        data = self.fatalities_series
        rolling_average = self.fatalities_per_day
        ylabel = 'Fatalities per Day'

        plotter = plots.DailyPlotter(gca, label, ylabel)
        plotter.summary_plot(data, rolling_average, per_capita, self.population)


    def dailyhospitalizationplot(self, per_capita=False, gca=None, label=None):
        ''' Summary plot of daily VOVID-19 hospitalizations. Plots bar plot of
        raw data behind a rolling average. Rolling average window and date range
        of data during class instantiation.
        
        Arguments:
            per_capita: Plot data per 100k residents
            gca: Existing matplotlib axes to plot two (optional)
            label: Custom label for data legend. Uses name attribute by default
        '''
        if label is None:
            label = self.name
        data = self.hospitalizations_series
        rolling_average = self.hospitalizations_per_day
        ylabel = 'Hospitalizations per Day'

        plotter = plots.DailyPlotter(gca, label, ylabel)
        plotter.summary_plot(data, rolling_average, per_capita, self.population)



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
        #TODO: Clean up exception handling
        try:
            self.population = JhuData().us_population(groupby='state').loc[self.name]
        except:
            self.population = np.nan
        self.get_params()


    def record_data(self):
        ''' Load raw data from combined covid data in Github repo
        or in local repo.

        Attributes that are recorded:
            positive cases
            fatalities
            hospitalizations
            percentage of population fully vaccinated
            percentage of population receiving at least partial dose
        '''

        #TODO: Needs capability to load from database module directly without csv dependency
        try:
            url = Path('https://raw.githubusercontent.com/lucascarter0')
            url = url.joinpath('covid19-analytics/master/us_combined_covid_data.csv')
            all_data = pd.read_csv(url)
        except:
            all_data = pd.read_csv('us_combined_covid_data.csv')
        all_data = all_data.set_index(['state', 'date'])

        self._record(self._load(all_data['total_cases']),
                     attrname='cases')
        self._record(self._load(all_data['total_deaths']),
                     attrname='fatalities')
        self._record(self._load(all_data['total_hospitalizations']),
                     attrname='hospitalizations')
        self._record(self._load(all_data['series_complete_yes']),
                     attrname='fully_vaccinated')
        self._record(self._load(all_data['administered_dose1_recip']),
                     attrname='partial_plus_vaccinated')



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
