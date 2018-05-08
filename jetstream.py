#!/usr/bin/env python3

"""
jetstream.py makes beautiful maps of the atmospheric jet stream.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

__version__ = "0.1"
__author__ = "Geert Barentsen (geert@barentsen.be)"
__copyright__ = "Copyright 2014 Geert Barentsen"

import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib import colors
from mpl_toolkits import basemap
from pydap import client
import netCDF4
import numpy as np
import datetime
import sys, os

A = {'r': 52/255., 'g': 152/255., 'b': 219/255.}  # blue
B = {'r': 231/255., 'g': 76/255., 'b': 60/255.}   # red
C = {'r': 241/255., 'g': 196/255., 'b': 15/255.}  # orange

COLORMAP = colors.LinearSegmentedColormap('jetstream',
                                          {'red':   [(0.0, 1.0, 1.0),
                                                     (0.25, A['r'], A['r']),
                                                     (0.75, B['r'], B['r']),
                                                     (1.0, C['r'], C['r'])],
                                           'green': [(0.0, 1.0, 1.0),
                                                     (0.25, A['g'], A['g']),
                                                     (0.75, B['g'], B['g']),
                                                     (1.0, C['g'], C['g'])],
                                           'blue':  [(0.0, 1.0, 1.0),
                                                     (0.25, A['b'], A['b']),
                                                     (0.75, B['b'], B['b']),
                                                     (1.0, C['b'], C['b'])],
                                           'alpha': [(0.0, 0.0, 0.0),
                                                     (0.15, 1.0, 1.0),
                                                     (1.0, 1.0, 1.0)]})

class JetStreamMap():

    def __init__(self, lon1=-140, lon2=40, lat1=20, lat2=70):
        self.lon1, self.lon2 = lon1, lon2
        self.lat1, self.lat2 = lat1, lat2

    def render(self, data, vmin=80, vmax=220, title=None):
        # self.fig = plt.figure(figsize=(9, 9*(9/16.)))
        self.fig = plt.figure(figsize=(10, 5))
        self.fig.subplots_adjust(0.05, 0.15, 0.95, 0.88,
                                 hspace=0.0, wspace=0.1)
        self.map = basemap.Basemap(projection='cyl',
                                   llcrnrlon=self.lon1, llcrnrlat=self.lat1,
                                   urcrnrlon=self.lon2, urcrnrlat=self.lat2,
                                   resolution="c", fix_aspect=False)

        self.map.pcolormesh(data.lon, data.lat, data.windspeed,
                            cmap=COLORMAP, vmin=vmin, vmax=vmax, alpha=None)
        self.colorbar = self.map.colorbar(location='bottom',
                                          pad=0.1, size=0.25,
                                          ticks=[100, 150, 200, 250])
        self.colorbar.ax.set_xlabel('Average wind speed at 250 mb (km/h)',
                                    fontsize=16)
        self.map.drawcoastlines(color='#7f8c8d', linewidth=0.5)
        self.map.fillcontinents('#bdc3c7', zorder=0)
        self.fig.text(.05, .91, title, fontsize=24, ha='left')
        return self.fig


class JetStreamData():
    """Abstract base class"""

    def __init__(self):
        self.load()

    def create_map(self, level, timestr):
        if level == 250:
            title = "Jet Stream %s" % timestr
        else:
            title = "Winds %d mb %s" % (level, timestr)

        mymap = JetStreamMap(lon1=-180, lon2=180, lat1=-70, lat2=+74)
        # mymap = JetStreamMap(lon1=-134, lon2=-74, lat1=26, lat2=+52)
        mymap.render(self, title=title)
        return mymap

class ERAJetStreamData(JetStreamData):

    def __init__(self, filename, level=250):
        self.load(filename, level)

    def load(self, filename, level):
        self.data = netCDF4.Dataset(filename)

        # Find the index for the 250 hPa level
        # (though netCDF4 says data['level'] has units millibars
        # rather than hPa)
        for lev, millibars in enumerate(self.data['level']):
            if millibars == level:
                break
        else:
            print("No 250 hPa level")
            raise ValueError("No %d hPa level" % level)
        print("%d hPa level is at index %d" % (level, lev))
        self.level = level
        self.levindex = lev

    def calc_windspeed(self, idx):
        # times = netCDF4.num2date(data.variables['time'],
        # data.variables['time'].units)
        # print("times:", times)

        lon = self.data.variables['longitude'][:]
        lat = self.data.variables['latitude'][:]

        # Set a sensitivity factor
        if self.level == 250:    # jetstream, big winds
            sensitivity = 3.5
        else:                    # anywhere else, the winds are smaller
            sensitivity = 7.5

        windspeed = (sensitivity *
            np.sqrt(self.data.variables['u'][idx][self.levindex][:]**2
                    + self.data.variables['v'][idx][self.levindex][:]**2))
        print("Shapes: u", self.data.variables['u'].shape,
              ", v", self.data.variables['u'].shape,
              ", windspeed", windspeed.shape)

        # Only take the first element of the windspeed, the 250 hPa level
        # windspeed = windspeed[day]

        # Shift grid from 0 to 360 => -180 to 180
        windspeed, lon = basemap.shiftgrid(180, windspeed, lon, start=False)

        self.lon, self.lat, self.windspeed = lon, lat, windspeed
        print("Now windspeed shape is", windspeed.shape)

if __name__ == '__main__':
    level = 250     # 1000 for sea level, 775 for 7000'
    outdir = "output"

    if not os.path.exists(outdir):
        os.mkdir(outdir)
    elif not  os.path.isdir(outdir):
        print("Can't create dir %s: there's a file by that name" % outdir)
        sys.exit(1)

    JSdata = ERAJetStreamData('interim-world-2015-04-windspeed.nc', level)

    timeunits = JSdata.data['time'].units
    cal = JSdata.data['time'].calendar
    for i, t in enumerate(JSdata.data['time']):
        thedate = netCDF4.num2date(t, units=timeunits, calendar=cal)
        print("thedate:", thedate, type(thedate))
        timestr = thedate.strftime("%Y-%m-%d")

        JSdata.calc_windspeed(i)

        mymap = JSdata.create_map(level, timestr)

        mymap.fig.savefig('output/%s-%d.png' % (timestr, level), dpi=100)
        plt.close()

