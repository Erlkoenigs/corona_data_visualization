import requests
import json
from datetime import datetime
from datetime import timedelta
import matplotlib.pyplot as plt

epoch = datetime(1970, 1, 1, 0, 0, 0)
data_update = False  # fetch fresh data from sources? (RKI + JH (germany only))
# graph data within this interval:
date_interval = [
    datetime(2020, 3, 10).date(),
    datetime.today().date()
]
# list with every date within this interval
date_interval_length = (date_interval[1] - date_interval[0]).days
dates = [date_interval[1] - timedelta(days=x) for x in range(date_interval_length)]
dates.reverse()


# get the current data from pomber (JH) and save to file
def fetch_json_jh():
    data_source_url = 'https://pomber.github.io/covid19/timeseries.json'
    fetched_data = requests.get(data_source_url)
    fetched_data_json = fetched_data.json()
    with open('data/data_JH.json', 'w+') as datafile_jh:
        json.dump(fetched_data_json, datafile_jh)


def fetch_json_rki(offs):
    data_source_url = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_COVID19/FeatureServer/0' \
                      '/query?where=1%3D1&objectIds=&time=&resultType=none&outFields=ObjectId%2CAnzahlFall' \
                      '%2CAnzahlTodesfall%2CMeldedatum%2CBundesland%2CAltersgruppe%2CGeschlecht%2CLandkreis' \
                      '&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnDistinctValues' \
                      '=false&cacheHint=false&orderByFields=Meldedatum+asc&groupByFieldsForStatistics=&outStatistics' \
                      '=&having=&resultRecordCount=2000&sqlFormat=none&f=json&resultOffset=' + str(offs)
    fetched_data = requests.get(data_source_url)
    fetched_data_json = fetched_data.json()
    return fetched_data_json


# update data files
if data_update:
    # update jh data
    fetch_json_jh()

    # update rki data
    with open('data/data_rki.json', 'r') as datafile:
        # check if file has content
        one_char = datafile.read(1)  # read first character
        datafile.seek(0)  # set cursor back to beginning of file
        if one_char:
            # if yes, load as json
            data = json.load(datafile)
        else:
            # if no, create data variable, which will be dumped into file later
            data = {'data_list': []}

    entries_added = 0
    i = 0  # count the amount of requests to the server to limit them
    while True:
        offset = len(data['data_list'])
        new_data = fetch_json_rki(offset)
        entries_added += len(new_data['features'])
        # data['data_list'].append(new_data["features"])
        for entry in new_data['features']:
            data['data_list'].append(entry)
        offset += 2000
        i += 1
        if 'exceededTransferLimit' not in new_data:
            print('end of data reached')
            break
        if i > 3:
            print('too many requests')
            break
        if len(new_data['features']) == 0:
            print('empty data response')
            break
    print(str(entries_added) + ' new entries')
    if entries_added > 0:  # if there's new data, update the json file
        with open('data/data_RKI.json', 'w+') as datafile:
            json.dump(data, datafile)

# use data files
# rki
total_cases_rki_graph = [0] * len(dates)  # total cases for every day in the time interval
daily_infections_rki = [0] * len(dates)
daily_deaths_rki = [0] * len(dates)
total_cases_rki = 0  # total cases the rki knows of
with open('data/data_rki.json', 'r') as datafile:
    data = json.load(datafile)
    for entry in data['data_list']:
        total_cases_rki += int(entry['attributes']['AnzahlFall'])
        entry_date = (epoch + timedelta(milliseconds=entry['attributes']['Meldedatum'])).date()
        if entry_date in dates:
            i = dates.index(entry_date)
            total_cases_rki_graph[i] = total_cases_rki
            daily_infections_rki[i] += int(entry['attributes']['AnzahlFall'])
            daily_deaths_rki[i] += int(entry['attributes']['AnzahlTodesfall'])

# jh
total_cases_jh = [0] * len(dates)
daily_infections_jh = [0] * len(dates)
deaths_jh = [0] * len(dates)
total_recovered_jh = [0] * len(dates)
daily_recoveries_jh = [0] * len(dates)
active_cases_jh = [0] * len(dates)  # total - recovered - deaths
with open('data/data_JH.json', 'r') as datafile:
    data = json.load(datafile)
data_ger = data['Germany']
for entry in data_ger:
    entry_date = datetime.strptime(entry['date'], '%Y-%m-%d').date()
    if entry_date in dates:
        i = dates.index(entry_date)
        total_cases_jh[i] = entry['confirmed']
        total_recovered_jh[i] = entry['recovered']
        if i > 0:
            daily_infections = total_cases_jh[i] - total_cases_jh[i - 1]
            daily_recoveries = total_recovered_jh[i] - total_recovered_jh[i - 1]
        else:
            daily_infections = 0
            daily_recoveries = 0
        daily_infections_jh[i] = daily_infections
        daily_recoveries_jh[i] = daily_recoveries
        deaths_jh[i] = entry['deaths']
        active_cases_jh[i] = (total_cases_jh[i] - daily_infections_jh[i] - deaths_jh[i]) / 2
dates_jh = dates
while total_cases_jh[-1] == 0:
    dates_jh.pop()
    total_cases_jh.pop()
    daily_infections_jh.pop()
    deaths_jh.pop()
    total_recovered_jh.pop()
    daily_recoveries_jh.pop()
    active_cases_jh.pop()

plt.figure(figsize=(13, 5))
# plt.yscale('log')  # logarithmic y-axis
labels = []
for date in dates:
    labels.append(date.strftime('%d.%m'))
x_coordinates = list(range(0, len(dates)))
# rki
# plt.plot(dates, total_rki, 'r-', label="RKI total",)
# plt.plot(dates, daily_rki, 'r-', label="RKI new")
# plt.plot(dates, deaths_rki, label="RKI deaths")
# jh
# plt.plot(dates_jh, total_jh, label='JH total cases')
plt.plot(dates_jh, daily_infections_jh, label='JH daily infections')
plt.plot(dates_jh, deaths_jh, label='JH total deaths')
# plt.plot(dates_jh, recovered_jh, label='JH total recovered')
plt.plot(dates_jh, daily_recoveries_jh, label='JH daily recoveries')
plt.plot(dates_jh, active_cases_jh, label='JH active cases / 2')

# bar charts
width = 0.35
total_previous = [0]
for x in range(0, len(total_cases_rki_graph) - 1):
    total_previous.append(total_cases_rki_graph[x])
# p1 = plt.bar(x_coordinates, total_previous, width, bottom=daily)
# p2 = plt.bar(x_coordinates, daily, width)
# plt.ylabel('cases')
plt.title('corona cases per day')
plt.xticks(dates, labels, rotation='vertical')
# plt.legend((p1[0], p2[0]), ('total', 'new'))
plt.grid(True)
plt.style.use('seaborn-dark')
plt.legend()
plt.savefig('plot.svg')
print("finished")