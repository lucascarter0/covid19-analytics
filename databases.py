#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""
from datetime import date
from posixpath import join

import pandas as pd

import utils



class HealthGovData:

    __hospital_baseurl = 'https://healthdata.gov/resource/g62h-syeh.json'
    __vaccine_baseurl = 'https://data.cdc.gov/resource/unsk-b7fc.json'


    def __init__(self):
        days_of_pandemic = (date.today() - date(2020, 1, 1)).days
        self._parse_limit = len(utils.us_state_abbrev)*days_of_pandemic
        print('Initializing Healthcare.gov database')


    def _load(self, url):
        df = pd.read_json(url)
        df.date = pd.to_datetime(df.date)
        df = df.set_index('date').sort_index()
        return df


    def load_hosptializations(self):
        hospital_url = '{}?$limit={}'.format(self.__hospital_baseurl, self._parse_limit)

        df = self._load(hospital_url)
        df = summarize_hospitalizations(df)
        df['state'] = df['state'].map(utils.us_state_abbrev_inverse)
        return df


    def load_vaccinations(self):
        """ Load US vaccination data through HealthData.gov API. """
        vaccine_url = '{}?$limit={}'.format(self.__vaccine_baseurl, self._parse_limit)

        df = self._load(vaccine_url)
        df['state'] = df['location'].map(utils.us_state_abbrev_inverse)
        df = df.drop('location', axis=1)
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


    def _load_global_url(self, url):
        data = pd.read_csv(url, index_col=1)
        data = data.drop(self.__global_column_drop, axis=1)
        data = data.groupby('Country/Region').sum()

        return data


    def _load_us_url(self, url, groupby='county', drop=None):
        data = pd.read_csv(url, index_col=1)
        data = data.rename(columns=self.__column_rename)

        data = data.set_index(county_state_index(data))

        if groupby.lower() == 'state':
            data = data.groupby('State').sum()
            if drop is None:
                drop = self.__state_column_drop
            #TODO: Make sure this works as intended vs what's commented out
            to_drop = [column for column in drop if column in data.columns]
            data = data.drop(columns=to_drop)
            # for column in drop:
            #     if column in data.columns:
            #         data = data.drop(columns=drop)

        # Convert dates to datetime format if columns are only dates
        try:
            data.columns = pd.to_datetime(data.columns)
            data.columns.name = 'date'
        except TypeError:
            pass
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


    def us_population(self, groupby='county'):
        url = join(self._timeseries_baseurl,
                   'time_series_covid19_deaths_US.csv')
        df = self._load_us_url(url, groupby=groupby)
        return df['Population'] if 'Population' in df.columns else None



def county_state_index(data):
    """ Append state name to county in dataframe including county and state columns."""
    return data.County.str.cat(data.State, sep=', ')



def icu_utilization(df):
    numerator = df['adult_icu_bed_covid_utilization_numerator']
    denominator = df['adult_icu_bed_covid_utilization_denominator']
    return numerator.divide(denominator)



def summarize_hospitalizations(df):
    hospitalization_cols = ['previous_day_admission_adult_covid_confirmed',
                            'previous_day_admission_pediatric_covid_confirmed']
    hospitalizations = df.reset_index().set_index(['state', 'date'])[hospitalization_cols]
    groupby_state = hospitalizations.sum(axis=1).groupby('state')
    df['total_hospitalizations'] = groupby_state.cumsum().values
    df['icu_bed_utilization'] = icu_utilization(df)
    return df



def combine_databases(hospital_data, vaccine_data, jhu_cases, jhu_deaths):
    cases = jhu_cases.stack()
    cases.name = 'total_cases'
    cases = cases.reset_index()

    deaths = jhu_deaths.stack()
    deaths.name = 'total_deaths'
    deaths = deaths.reset_index()

    combined = pd.merge(hospital_data.reset_index(),
                        vaccine_data.reset_index(),
                        on=['state', 'date'])

    combined = pd.merge(combined, cases, on=['state', 'date'])
    combined = pd.merge(combined, deaths, on=['state', 'date'])
    return combined



def load_us_database(save=True):
    """ Combine HealthData.gov and JHU databases into combined dataframe
    at state-level resolution. If save option is set to true, will save
    as CSV in PWD."""
    hospitalizations = HealthGovData().load_hosptializations()
    vaccinations = HealthGovData().load_vaccinations()
    state_cases = JhuData().us_cases(groupby='state')
    state_fatalities = JhuData().us_fatalities(groupby='state')

    df = combine_databases(hospitalizations, vaccinations,
                           state_cases, state_fatalities)

    df = df.set_index('date')
    if save:
        df.to_csv('us_combined_covid_data.csv')

    return df
