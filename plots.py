# -*- coding: utf-8 -*-


import datetime

import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

import databases
import analytics



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
mpl.rcParams['ytick.direction'] = 'in'


class TimeSeriesPlotter:
    def __init__(self, ax=None, title=None, ylabel=None, fig=None):
        if ax is None:
            #TODO: Should fig be included?
            fig, ax = plt.subplots(figsize=(12, 5))
        self.fig = fig
        self.ax = ax
        self.title = title
        self.ylabel = ylabel

    def plot(self, data, **args):
        ''' Add line plot of data argument to axis. '''
        self.ax.plot(data, **args)
        self.axes_format()

    def bar_plot(self, groups, data, **args):
        ''' Add bar plot of data argument indexed by group to axis.'''
        self.ax.bar(groups, data, **args)
        self.axes_format()

    def axes_format(self):
        """ Internal method that applites plot settings
        and labels to figure."""
        self.ax.set_title(self.title)
        self.ax.set_xlabel('Date')
        self.ax.set_ylabel(self.ylabel)
        self.ax.set_ylim(bottom=0)
        axis_date_fmt(self.ax)



class DailyPlotter(TimeSeriesPlotter):
    def __init__(self, ax=None, title=None, ylabel=None):
        super().__init__(ax, title, ylabel)


    def summary_plot(self, data, rolling_average, per_capita=False, population=0):
        if per_capita:
            if population is None:
                raise ArithmeticError('Population value not defined for ' \
                                      'population normalization')
            data = analytics.normalize(data, population)
            rolling_average = analytics.normalize(rolling_average, population)
            self.ylabel += ' per Million Residents'

        self.plot(rolling_average)
        self.bar_plot(data.diff().index, data.diff(), width=1, alpha=0.25)



def series_window(series, start=None, end=None):
    """ Trim series to start/end window."""
    series = series[start:end]
    # if start:
    #     if end:
    #         series = series[start:end]
    #     else:
    #         series = series[start:]
    # else:
    #     if end:
    #         series = series[:end]
    return series



def axis_date_fmt(gca):
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
    plotter = TimeSeriesPlotter(fig, gca, title=ylabel, ylabel=ylabel)

    for entry in classes:
        series = getattr(entry, attr, None)
        if datatype.lower() != 'case fatality':
            series = analytics.normalize(series, population=entry.population, per=1000000)
        series = series_window(series, start, end)
        plotter.plot(series, label=entry.name)
        # gca.plot(series, label=entry.name, linewidth=2.5)
        plotter.ax.fill_between(series.index, series, alpha=0.25)
    plotter.ax.legend()

    plotter.ax.grid('off', which='both', axis='x')
    plotter.fig.tight_layout()





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
    # all_data = databases.load_us_database(save=False).reset_index()
    all_data = pd.read_csv('us_combined_covid_data.csv')
    all_data = all_data.set_index(['state', 'date'])

    # last_record = datetime.date.today() - datetime.timedelta(1)
    # vaccinations = all_data.xs(last_record.strftime('%Y-%m-%d'), level=1)['series_complete_yes']
    last_record = all_data.index[-1][1]
    vaccinations = all_data.xs(last_record, level=1)['series_complete_yes']

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

    _, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(new_df['total_vaccinated'], case_fatality)
    ax.set_xlabel('Percentage of Population Fully Vaccinated')
    # ax.set_ylabel('Hospitalizations since {}\n(Scaled for Population)'.format(last_month.strftime('%m/%d/%Y')))
    ax.set_ylabel('Case Fatality')