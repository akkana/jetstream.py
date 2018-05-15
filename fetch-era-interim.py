#!/usr/bin/env python3

'''Fetch jetstream (and other wind) data from ECMWFDataServer.
   Uses the ECMWF Web API:
   https://software.ecmwf.int/wiki/display/WEBAPI/ECMWF+Web+API+Home
   installable through pip: go to
   https://software.ecmwf.int/wiki/display/WEBAPI/Web-API+Downloads
   and click on "Click here to see the installation/update instructions..."

   You will need to register for an API key and put it in your ~/.ecmwfapirc
   then go to
   http://apps.ecmwf.int/datasets/data/interim-full-daily/levtype=sfc/
   (or equivalent page for the dataset you need)
   and request the data you want. You can fetch the data via
   the web interface, or click on "View the MARS request" to get
   parameters you can plug into this Python script.

   If making multiple requests, be sure to read about request efficiency:
   https://software.ecmwf.int/wiki/display/WEBAPI/Retrieval+efficiency
'''

from ecmwfapi import ECMWFDataServer

import datetime

# Retrieves U and V components, vertical velocity and vorticity
# for levels 1000, 775, and 250 hPa, for the whole world.
# area is North/West/South/East; for North America, try something like
#        'area'      : '52/-134/26/-74',
def fetch_daily_wind_data(start_date, end_date, levels, area):
    server = ECMWFDataServer()
    request = {
        "class": "ei",
        "dataset": "interim",
        "date": "%s/to/%s" % (start_date.strftime('%Y-%m-%d'),
                                end_date.strftime('%Y-%m-%d')),
                # "2015-04-01/to/2015-04-30",
        "expver": "1",
        "grid": "0.75/0.75",
        "levelist": '/'.join([str(l) for l in levels]),
                # "levelist": "250/775/1000",
        "levtype": "pl",
        "param": "131.128/132.128/135.128/138.128",
        "step": "0",
        "stream": "oper",
        "time": "18:00:00",
        "area": '/'.join([str(a) for a in area]),
                # North/West/South/East.
        "type": "an",
        'format': "netcdf",
        "target": "us-windspeed-interim.nc",
    }
    print(request)
    server.retrieve(request)

def fetch_averages_for_date_range(dates, levels, area):
    '''
    dates is a list of either string, 20150101, or datetime.
    levels is a list of millibars
    area is [north, west, south, east]
    '''
    for i, d in enumerate(dates):
        if type(d) is not str:
            dates[i] = d.strftime('%Y%m%d')
            # "20150101/20150201/..."
    request = {
        "class": "ei",
        "dataset": "interim",
        "date": '/'.join(dates),
        "expver": "1",
        "grid": "0.75/0.75",
        "levelist": '/'.join([str(l) for l in levels]),
        "levtype": "pl",
        "param": "130.128/131.128/132.128/135.128/138.128",
        "stream": "moda",
        "area": '/'.join([str(a) for a in area]),
        # North/West/South/East.
        "type": "an",
        'format': "netcdf",
        "target": "averages.nc",
    }
    print(request)

    server = ECMWFDataServer()
    server.retrieve(request)

if __name__ == '__main__':
    if True:
        fetch_daily_wind_data(datetime.datetime(2011, 1, 1),
                              datetime.datetime(2018, 1, 1),
                              levels=[250, 775, 1000],
                              # area is North/West/South/East.
                              area=[ 62, -138, 15, -55 ])

    else:
        daterange = []
        for year in range(2010, 2018):
            for month in range(1, 13):
                daterange.append(datetime.datetime(year, month, 1))
        fetch_averages_for_date_range(dates=daterange,
                                      levels=[250, 775, 1000],
                                      # area is North/West/South/East.
                                      area=[ 62, -138, 15, -55 ])
