# -*- coding: utf-8 -*-
"""
TODO: Make this cleaner and generalize interface
"""

import pandas as pd
from posixpath import join
from datetime import date, timedelta


class Country:

    def __init__(self, name, start_date=None, end_date=None):
        self.url = 'https://raw.githubusercontent.com/'
        self.url = join(self.url, 'CSSEGISandData/COVID-19')
        self.url = join(self.url, 'master','csse_covid_19_data')
        self.url = join(self.url, 'csse_covid_19_time_series')

        self.start_date = start_date
        self.end_date = end_date
        self.name = name
        self.country = name

        url = join(self.url, 'time_series_covid19_confirmed_global.csv')
        self.confirmed = self.load_series(url)
        self.dconfirmed = self._diff(self.confirmed)
        
        url = join(self.url, 'time_series_covid19_deaths_global.csv')
        self.deaths = self.load_series(url)
        self.ddeaths = self._diff(self.deaths)
        
        url = join(self.url, 'time_series_covid19_recovered_global.csv')
        self.recovered = self.load_series(url)
        self.drecovered = self._diff(self.recovered)

        self.population()

    def _diff(self, df, window=7):
        return df.diff().rolling(window=window).mean()


    def _fmt_index(self, index):
        return pd.to_datetime(index, infer_datetime_format=True)


    def population(self):
        url = 'https://raw.githubusercontent.com/lucascarter0/data-science-tools/master/COVID19/un_population_by_country.csv'
        df = pd.read_csv(url, index_col=1)
        df = self._countryname_remap(df)
        # Scale to full value
        df = df.apply(lambda x : x*1000)
        self.population = df.loc[self.country, 'PopTotal']
        self.population_density = df.loc[self.country, 'PopDensity']
        
    def _countryname_remap(self, df):
        df.loc['United States'] = df.loc['United States of America']
        df.loc['US'] = df.loc['United States of America']
        return df

        
    def load_series(self, url):
        df = pd.read_csv(url, index_col=1)
        
        # Index on country name
        df = df.loc[self.country]
        # Drop indices of series that are not dates
        df = df.drop(['Province/State','Lat', 'Long'])
        # Convert index to DateTime
        df.index = self._fmt_index(df.index)

        # Return dates between start date and end date
        return df.loc[self.start_date:self.end_date]
        




class State:
    
    def __init__(self, index, start_date=date(2020,4,12), end_date=date.today()):
        
        self.start_date = start_date
        self.end_date = end_date
        df = self.load_dataframe(index)
        
        for ii in df.columns:
            setattr(self, ii.lower(), df[ii])
            
        self.load_confirmed_deaths(index)
            
        print('csse_covid_19_daily_reports_us for {}'.format(index))
        
    def load_dataframe(self, index):
    
        df = pd.DataFrame(columns=['Confirmed','Deaths',
                                     'Recovered','Active','People_Tested',
                                     'People_Hospitalized'])

        dates = [ii.strftime('%m-%d-%Y') for ii in daterange(self.start_date, self.end_date)]
    
        for single_date in dates:
            #day = single_date.strftime('%m-%d-%Y')
            basepath = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us'
            url = join(basepath, '{}.csv'.format(single_date))
            a = pd.read_csv(url, index_col=0, 
                            usecols=['Province_State','Confirmed','Deaths',
                                     'Recovered','Active','People_Tested',
                                     'People_Hospitalized'])
          
            df.loc[single_date] = a.loc[index]
        df.index = pd.to_datetime(df.index)
        return df.astype('float64')
    
    def daily_case_plot(self, window=7, normed=False):
        if normed:
            s = self.confirmed.divide(self.people_tested)
        else:
            s = self.confirmed
        s.diff().rolling(window=window).mean().plot()
        
    def load_confirmed_deaths(self, index):
        url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv'
        df = pd.read_csv(url)
        df = df.loc[ df['Province_State'] == index]
        df = df.drop(['UID', 'iso2','iso3','code3','FIPS','Admin2','Country_Region',
                'Lat','Long_','Combined_Key'], axis=1)
        df = df.set_index('Province_State', drop=True)
        df = df.sum()
        df.index = pd.to_datetime(df.index)
        self.confirmed = df
        
        # url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv'
        # df = pd.read_csv(url)
        # df = df.loc[ df['Province_State'] == index]
        # df = df.drop(['UID', 'iso2','iso3','code3','FIPS','Admin2','Country_Region',
        #         'Lat','Long_','Combined_Key'], axis=1)
        # df = df.set_index('Province_State', drop=True)
        # df = df.sum()
        # df.index = pd.to_datetime(df.index)
        # self.deaths = df


def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

# population = 2636000
# df = df.apply(lambda x : x / population)
# df.tail()



#a = Confirmed()
#a.load_county('Cleburne, Alabama, US')
#b = Confirmed()
# a = Country('Sweden')
a = State('Texas')
# b = State('Florida')
# c = State('New York')
#a.load_country('Russia')
#a._diff()