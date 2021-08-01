# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 10:16:52 2021

@author: lucas
"""

from posixpath import join

import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

from countryinfo import CountryInfo

import utils
from covid_databases import JhuData
plt.style.use('seaborn')

# def load_us(self):
#     return self.record(self.raw_data.groupby('date').sum())

# def load_state(self, state):
#     state = us_state_abbrev.get(state)
#     df = self.raw_data
#     df = df.loc[df.state == state].drop('state', axis=1)
#     return self.record(df)

# data['total_hospitalizations'] = data['hospitalizations_per_day'].sum()
# data['icu_bed_utilization_per_day'] = df['adult_icu_bed_covid_utilization_numerator'].divide(df['adult_icu_bed_covid_utilization_denominator'])
# data['icu_bed_utilization'] = data['icu_bed_utilization_per_day'].iloc[-1]



mpl.rcParams['axes.facecolor'] = 'white'
mpl.rcParams['axes.grid'] = True
mpl.rcParams['axes.grid.axis'] = 'y'
mpl.rcParams['axes.grid.which'] = 'both'
mpl.rcParams['axes.spines.left'] = False
mpl.rcParams['axes.spines.right'] = False
mpl.rcParams['axes.spines.top'] = False
mpl.rcParams['axes.spines.bottom'] = False
mpl.rcParams['grid.color'] = '#efeff2'
mpl.rcParams['lines.linewidth'] = 2
mpl.rcParams['lines.linestyle'] = '-'
mpl.rcParams['xtick.direction'] = 'in'
mpl.rcParams['xtick.labelsize'] = 11
mpl.rcParams['xtick.major.size'] = 6
mpl.rcParams['xtick.minor.size'] = 6
mpl.rcParams['ytick.labelsize'] = 11
mpl.rcParams['ytick.major.size'] = 0



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

        plot_series(data, rolling_average, label, ylabel, gca)


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

        plot_series(data, rolling_average, label, ylabel, gca)


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

        all_data = JhuData()
        self._record(self._load(all_data.us_cases(groupby='state')), 'cases')
        data = self.getpopulation(all_data.us_fatalities(groupby='state'))
        self._record(self._load(data), 'fatalities')

        self.get_params()

    def getpopulation(self, data):
        if 'Population' in data.columns:
            self.population = data.loc[self.name, 'Population']
            data = data.drop('Population', axis=1)
        return data

    def _load_healthcare_gov_data(self):
        pass



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


def plot_series(data, rolling_average, label, ylabel, gca=None):
    fig = None
    if gca is None:
        fig, gca = plt.subplots(figsize=(15, 5))

    gca.bar(data.diff().index, data.diff(), width=1,
            color='black', alpha=0.25)
    gca.plot(rolling_average, c='black')
    gca.set_title('{}\n{}'.format(label, ylabel))
    __axis_date_fmt(gca)
    gca.set_ylim(bottom=0)
    gca.tick_params(axis='y', direction="in")
    gca.locator_params(axis='y', nbins=4)
    if fig is not None:
        fig.tight_layout()



def series_window(series, start=None, end=None):
    """ Trim series to start/end window."""
    if start:
        if end:
            series = series[start:end]
        else:
            series = series[start:]
    else:
        if end:
            series = series[:end]
    return series



def __axis_date_fmt(gca):
    gca.xaxis.set_major_locator(mpl.dates.YearLocator())
    gca.xaxis.set_major_formatter(mpl.dates.DateFormatter('%b-%Y'))
    gca.xaxis.set_minor_locator(mpl.dates.MonthLocator())
    gca.xaxis.set_minor_formatter(mpl.dates.DateFormatter('%b'))
    return gca



def plot_compare(classes, datatype, figsize=(12, 5), start=None, end=None):

    if datatype.lower() == 'cases':
        attr = 'cases_per_day'
        ylabel = 'Daily Cases per Million Residents'
    elif datatype.lower() == 'fatalities':
        attr = 'fatalities_per_day'
        ylabel = 'Daily Deaths per Million Residents'
    elif datatype.lower() == 'case fatality':
        attr = 'case_fatality_series'
        ylabel = 'Case Fatality'
    else:
        raise TypeError('Datatype {} not supported for comparison'.format(datatype))

    fig, gca = plt.subplots(figsize=figsize, dpi=80)

    for entry in classes:
        series = getattr(entry, attr, None)
        if datatype.lower() != 'case fatality':
            series = normalize(series, population=entry.population, per=1000000)
        series = series_window(series, start, end)
        gca.plot(series, label=entry.name, linewidth=2.5)
        gca.fill_between(series.index, series, alpha=0.25)
    gca.legend()

    gca.set_xlabel('Date')
    gca.set_ylabel(ylabel)
    gca.locator_params(axis='y', nbins=4)
    __axis_date_fmt(gca)
    gca.grid('off', which='both', axis='x')
    fig.tight_layout()

# mpl.rcParams.update(mpl.rcParamsDefault)

# texas = State('Texas')
# alabama = State('Alabama')
# florida = State('Florida')
# japan = Country('Japan')

# plot_compare([texas, florida, japan], 'fatalities', figsize=(10, 5))

# norway = Country('Norway')
# sweden = Country('Sweden')
# uk = Country('Finland')


# plot_compare([norway, sweden, uk], 'fatalities', figsize=(10, 5))
plot_compare([Country(ii) for ii in utils.G7_COUNTRIES], 'fatalities', figsize=(10, 5))
