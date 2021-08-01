# -*- coding: utf-8 -*-
"""
"""
from datetime import date
from posixpath import join

import pandas as pd

import utils


class HealthGovData:
    __baseurl = 'https://healthdata.gov/resource/g62h-syeh.json'

    __hospitalization_cols = ['previous_day_admission_adult_covid_confirmed',
                         'previous_day_admission_pediatric_covid_confirmed']

    def __init__(self):
        days_of_pandemic = (date.today() - date(2020, 1, 1)).days
        self._parse_limit = len(utils.us_state_abbrev)*days_of_pandemic
        self.url = '{}?$limit={}'.format(self.__baseurl, self._parse_limit)

    def load(self):
        print('Initializing Healthcare.gov database')
        df = pd.read_json(self.url)
        df.date = pd.to_datetime(df.date)
        df = df.set_index('date').sort_index()
        df = self.append_summary(df)
        df['state'] = df['state'].map(utils.us_state_abbrev_inverse)
        return df

    def append_summary(self, df):

        df['hospitalizations_per_day'] = df[self.__hospitalization_cols].sum(axis=1)
        df['icu_bed_utilization'] = icu_utilization(df)
        return df



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

    def _load_us_url(self, url, groupby='county', drop=None):
        data = pd.read_csv(url, index_col=1)
        data = data.rename(columns=self.__column_rename)

        data = data.set_index(self.__county_index(data))

        if groupby.lower() == 'state':
            data = data.groupby('State').sum()
            if drop is None:
                drop = self.__state_column_drop
            data = data.drop(columns=drop)

        data.columns = pd.to_datetime(data.columns)
        data.columns.name = 'date'
        data.index.name = groupby

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
        to_drop = self.__state_column_drop.append('Population')
        return self._load_us_url(url, groupby=groupby, drop=to_drop)


def icu_utilization(df):
    numerator = df['adult_icu_bed_covid_utilization_numerator']
    denominator = df['adult_icu_bed_covid_utilization_denominator']
    return numerator.divide(denominator)



def combine_databases(hospital_data, jhu_cases, jhu_deaths):
    cases = jhu_cases.stack()
    cases.name = 'total_cases'
    cases = cases.reset_index()

    deaths = jhu_deaths.stack()
    deaths.name = 'total_deaths'
    deaths = deaths.reset_index()

    combined = pd.merge(hospital_data.reset_index(), cases, on=['state', 'date'])
    combined = pd.merge(combined, deaths, on=['state', 'date'])
    return combined


def update_us_csv():

    a = HealthGovData().load()
    df1 = JhuData().us_cases(groupby='state')
    df2 = JhuData().us_fatalities(groupby='state')

    df = combine_databases(a, df1, df2)
    df = df.set_index('date')
    df.to_csv('us_combined_covid_data.csv')