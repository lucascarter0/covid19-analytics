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
plt.style.use('seaborn')



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



class JhuData():

    __column_rename = {'Admin2': 'County',
                       'Province_State': 'State',
                       'Country_Region': 'Country',
                       'Lat': 'Latitude',
                       'Long_': 'Longitude'}

    __global_column_drop = ['Lat', 'Long', 'Province/State']
    __state_column_drop = ['UID', 'code3', 'FIPS', 'Latitude', 'Longitude']

    def __init__(self):

        self.__baseurl = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data'
        self._timeseries_baseurl = join(self.__baseurl,
                                        'csse_covid_19_time_series')
        self._daily_report_baseurl = join(self.__baseurl,
                                          'csse_covid_19_daily_reports_us')

    def __county_index(self, data):
        return data.County.str.cat(data.State, sep=', ')

    def _load_global_url(self, url):
        data = pd.read_csv(url, index_col=1)
        data = data.drop(self.__global_column_drop, axis=1)
        data = data.groupby('Country/Region').sum()
        return data

    def _load_us_url(self, url, groupby='county'):
        data = pd.read_csv(url, index_col=1)
        data = data.rename(columns=self.__column_rename)

        data = data.set_index(self.__county_index(data))

        if groupby.lower() == 'state':
            data = data.groupby('State').sum()
            data = data.drop(columns=self.__state_column_drop)

        return data


    def global_cases(self):
        url = join(self._timeseries_baseurl,
                   'time_series_covid19_confirmed_global.csv')
        return self._load_global_url(url)


    def global_fatalities(self):
        url = join(self._timeseries_baseurl,
                   'time_series_covid19_deaths_global.csv')
        return self._load_global_url(url)


    def us_cases(self, groupby='county'):
        url = join(self._timeseries_baseurl,
                   'time_series_covid19_confirmed_US.csv')
        return self._load_us_url(url, groupby=groupby)


    def us_fatalities(self, groupby='county'):
        url = join(self._timeseries_baseurl,
                   'time_series_covid19_deaths_US.csv')
        return self._load_us_url(url, groupby=groupby)



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



G7_COUNTRIES = ['Japan', 'Canada', 'Germany', 'Italy',
                'France', 'United Kingdom', 'US']


EUROPEAN_UNION = ['Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus',
                  'Czech Republic', 'Denmark', 'Estonia', 'Finland', 'France',
                  'Germany', 'Greece', 'Hungary', 'Ireland', 'Italy', 'Latvia',
                  'Lithuania', 'Luxembourg', 'Malta', 'Netherlands', 'Poland',
                  'Portugal', 'Romania', 'Slovakia', 'Slovenia', 'Spain',
                  'Sweden']


G20_COUNTRIES = ['Argentina', 'Australia', 'Brazil', 'Canada', 'China',
                 'France', 'Germany', 'India', 'Indonesia', 'Italy', 'Japan',
                 'Korea, South', 'Mexico', 'Russia', 'Saudi Arabia',
                 'South Africa', 'Turkey', 'United Kingdom', 'US']



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
plot_compare([Country(ii) for ii in G20_COUNTRIES], 'fatalities', figsize=(10, 5))
