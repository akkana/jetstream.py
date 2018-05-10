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
   and request the data you want. You can fetch the data via
   the web interface, or click on "View the MARS request" to get
   parameters you can plug into this Python script.

   If making multiple requests, be sure to read about request efficiency:
   https://software.ecmwf.int/wiki/display/WEBAPI/Retrieval+efficiency
'''

from ecmwfapi import ECMWFDataServer

# Retrieves U and V components, vertical velocity and vorticity
# for levels 1000, 775, and 250 hPa, for the whole world.
# area is North/West/South/East; for North America, try something like
#        'area'      : '52/-134/26/-74',
def fetch_wind_data():
    server = ECMWFDataServer()
    server.retrieve({
        "class": "ei",
        "dataset": "interim",
        "date": "2015-04-01/to/2015-04-30",
        "expver": "1",
        "grid": "0.75/0.75",
        "levelist": "250/775/1000",
        "levtype": "pl",
        "param": "131.128/132.128/135.128/138.128",
        "step": "0",
        "stream": "oper",
        "time": "18:00:00",
        "type": "an",
        'format'    : "netcdf",
        "target": "interim-world-2015-04-windspeed.nc",
    })

if __name__ == '__main__':
    fetch_wind_data()
