# -*- coding: utf-8 -*-
"""
"""

import datetime

import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

import databases
import analytics
# from analytics import State



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
    elif datatype.lower() == 'hospitalizations':
        attr = 'hospitalizations_per_day'
        ylabel = 'Daily Hospitalizations per Million Residents'
    else:
        raise TypeError('Datatype {} not supported for comparison'.format(datatype))

    fig, gca = plt.subplots(figsize=figsize, dpi=80)

    for entry in classes:
        series = getattr(entry, attr, None)
        if datatype.lower() != 'case fatality':
            series = analytics.normalize(series, population=entry.population, per=1000000)
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

# norway = COVID19.Country('Norway')
# sweden = COVID19.Country('Sweden')
# uk = COVID19.Country('Finland')

# plot_compare([norway, sweden, uk], 'fatalities', figsize=(10, 5))
# plot_compare([Country(ii) for ii in utils.G7_COUNTRIES], 'fatalities', figsize=(10, 5))
# plot_compare([analytics.State(ii) for ii in ['Alabama', 'Texas', 'Florida', 'Massachusetts']], 'hospitalizations', figsize=(10, 5))

def corr_plot():
    # all_data = pd.read_csv('https://raw.githubusercontent.com/lucascarter0/covid19-analytics/master/us_combined_covid_data.csv')
    all_data = databases.load_us_database(save=False).reset_index()
    all_data = all_data.set_index(['state', 'date'])
    
    last_record = datetime.date.today() - datetime.timedelta(1)
    vaccinations = all_data.xs(last_record.strftime('%Y-%m-%d'), level=1)['series_complete_yes']
    population = databases.JhuData().us_population(groupby='state')
    
    last_month = last_record - pd.DateOffset(weeks=8)
    new_df = all_data.reset_index()
    new_df['date'] = pd.to_datetime(new_df['date'])
    new_df = new_df.loc[new_df['date'] == pd.to_datetime(last_record)].set_index('state') - new_df.loc[new_df['date'] == last_month].set_index('state')
    new_df = new_df[['total_hospitalizations', 'total_deaths', 'total_cases']]
    new_df['total_vaccinated'] = vaccinations
    
    case_fatality = new_df['total_deaths'].divide(new_df['total_cases'])
    
    population = population.drop([ii for ii in population.index if ii not in new_df.index], axis=0)
    for column in new_df.columns:
        new_df[column] = new_df[column].divide(population)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(new_df['total_vaccinated'], case_fatality)
    ax.set_xlabel('Percentage of Population Fully Vaccinated')
    # ax.set_ylabel('Hospitalizations since {}\n(Scaled for Population)'.format(last_month.strftime('%m/%d/%Y')))
    ax.set_ylabel('Case Fatality')