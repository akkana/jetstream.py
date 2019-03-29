#!/usr/bin/env python3

"""
jetstream.py makes beautiful maps of the atmospheric jet stream
using wind data from ECMWF.int.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

__version__ = "0.2"
__author__ = "Akkana Peck (akkana@shallowsky.com), Geert Barentsen (geert@barentsen.be)"
__copyright__ = "Copyright 2018 Akkana Peck, 2014 Geert Barentsen"
__license__ = "MIT"

import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib import colors
from mpl_toolkits import basemap
import numpy as np

import netCDF4

import datetime
import argparse
import math
import sys, os

# Decide on a cache directory
try:
    import xdg.BaseDirectory
    CACHEDIR = os.path.join(xdg.BaseDirectory.xdg_cache_home, "ECMWF")
except:
    print("Can't import xdg, will look for data in current directory")
    CACHEDIR = '.'

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
                                           # Alpha that sets land to grey,
                                           # water to white:
                                           'alpha': [(0.0, 0.0, 0.0),
                                                     (0.15, 1.0, 1.0),
                                                     (1.0, 1.0, 1.0)]})

class JetStreamMap():

    def __init__(self, lon1=-140, lon2=-40, lat1=20, lat2=70):
        self.lon1, self.lon2 = lon1, lon2
        self.lat1, self.lat2 = lat1, lat2

    def render(self, data, vmin=30, vmax=220, title=None):

        # I haven't found any way to get basemap to tell us the aspect ratio,
        # or to specify only one and let basemap calculate the other:
        # self.fig = plt.figure(figsize=(9, 6))
        # So just don't specify; basemap will give us something
        # that comes out 640px at 100dpi.
        self.fig = plt.figure()

        self.fig.subplots_adjust(0.05, 0.15, 0.95, 0.88,
                                 hspace=0.0, wspace=0.1)

        self.map = basemap.Basemap(projection='cyl',
                                   llcrnrlon=self.lon1, llcrnrlat=self.lat1,
                                   urcrnrlon=self.lon2, urcrnrlat=self.lat2,
                                   resolution="c", fix_aspect=True)

        self.map.pcolormesh(data.lon, data.lat, data.windspeed,
                            cmap=COLORMAP, vmin=vmin, vmax=vmax, alpha=None)
        self.colorbar = self.map.colorbar(location='bottom',
                                          pad=0.1, size=0.25,
                                          ticks=[100, 150, 200, 250])
        self.colorbar.ax.set_xlabel('Average wind speed at 250 mb (km/h)',
                                    fontsize=16)

        self.map.drawcoastlines(color='#7f8c8d', linewidth=0.5)
        self.map.fillcontinents('#bdc3c7', zorder=0)
        self.map.drawcountries(color='#7f8c8d', linewidth=0.5)
        self.map.drawstates(color='#7f8c8d', linewidth=0.5)
        self.fig.text(.05, .91, title, fontsize=24, ha='left')
        return self.fig


class JetStreamData():
    """Abstract base class, in case other data sources turn up"""

    def __init__(self):
        self.load()

    def create_map(self, level, timestr, west, east, south, north):
        if level == 250:
            title = "Jet Stream %s" % timestr
        else:
            title = "Winds %d mb %s" % (level, timestr)

        mymap = JetStreamMap(lon1=west, lon2=east, lat1=south, lat2=north)

        mymap.render(self, title=title)
        return mymap

class ERAJetStreamData(JetStreamData):

    def __init__(self, filename):
        if os.path.exists(filename):
            self.datafile = filename
        else:
            self.datafile = os.path.join(CACHEDIR, filename)
            if not os.path.exists(self.datafile):
                raise IOError(2, "Data file doesn't exist", filename)

        self.data = netCDF4.Dataset(self.datafile)

    def list_data(self):
        dic = {}
        for key in self.data.variables:
            vals = self.data[key][:]

            if key == 'time':
                timeunits = JSdata.data['time'].units
                cal = JSdata.data['time'].calendar
                starttime = netCDF4.num2date(vals[0], units=timeunits,
                                             calendar=cal)
                endtime = netCDF4.num2date(vals[-1], units=timeunits,
                                           calendar=cal)
                dic[key] = "%d values, ranging from %s to %s" % \
                            (len(vals),
                             starttime.strftime("%Y-%m-%d"),
                             endtime.strftime("%Y-%m-%d"))

            elif isinstance(vals, np.ndarray):
                if len(vals.shape) == 1:
                    if vals.shape[0] < 10:
                        dic[key] = vals
                    else:
                        dic[key] = '%d values ranging from %s to %s' %\
                                   (vals.shape[0],
                                    str(min(vals)), str(max(vals)))
                else:
                    dic[key] = "ndarray of shape %s" % str(vals.shape)

            elif len(vals) < 10:
                dic[key] = vals

            elif type(vals[0]) is int or type(vals[0]) is np.int32:
                dic[key] = "%s: ranging from %d to %d" % (key, min(vals),
                                                          max(vals))
            elif type(vals[0]) is float or type(vals[0]) is np.float32:
                dic[key] = "%s: ranging from %f to %f" % (key, min(vals),
                                                          max(vals))
            else:
                dic[key] = '%s: type %s' % (key, str(type(vals[0])))

        return dic
        # return self.data['level'][:]

    def calc_windspeed(self, idx, level, threshold=0):
        # times = netCDF4.num2date(data.variables['time'],
        # data.variables['time'].units)
        # print("times:", times)

        # Find the index for the appropriate pressure level
        for levindex, millibars in enumerate(self.data['level']):
            if millibars == level:
                break
        else:
            raise ValueError("No %d hPa level (maybe check with -L?)" % level)

        lon = self.data.variables['longitude'][:]
        lat = self.data.variables['latitude'][:]

        # Set a threshold or sensitivity factor
        if not threshold:
            if level == 250:         # jetstream, big winds
                threshold = 3.0
            else:                    # anywhere else, the winds are smaller
                threshold = 7.5

        windspeed = (threshold *
            np.sqrt(self.data.variables['u'][idx][levindex][:]**2
                    + self.data.variables['v'][idx][levindex][:]**2))

        # Shift grid from 0 to 360 => -180 to 180
        # windspeed, lon = basemap.shiftgrid(180, windspeed, lon, start=False)

        self.lon, self.lat, self.windspeed = lon, lat, windspeed

if __name__ == '__main__':

    def parse_args():
        """Parse commandline arguments."""
        parser = argparse.ArgumentParser()

        parser.add_argument('-t', '--threshold', action='store',
                            dest='threshold', type=float, default=0.0,
                            help="Threshold. Defaults to 3.0 for the jetstream"
                                 " and 7.5 for any other level.")
        parser.add_argument('-a', '--area', action='store',
                            type=int, nargs=4,
                            dest='area', default=[0, 0, 0, 0],
                            metavar=("west", "east", "south", "north"),
                            help="Area to plot"
                                 " (default: everything in the dataset.) "
                                 "For world, -180 180 -70 74; "
                                 "for North America try -a -138 -55 15 62).")
        parser.add_argument('-l', '--level', action='store', dest='level',
                            type=int, default=250,
                            help="Pressure level to plot, in millibars."
                                 " 1000 for sea level, 775 for 7000 feet,"
                                 " 250 for the jetstream")
        parser.add_argument('-o', '--outdir', action='store', dest='outdir',
                            default=None,
                            help="Output directory (will be created if needed)")
        parser.add_argument('-d', '--dpi', action='store', dest='dpi',
                            type=int, default=150,
                            help="DPI to save images (default 150)")

        parser.add_argument('-L', '--list-data', action="store_true",
                            default=False, dest='listdata',
                            help="List values available in the data file")

        parser.add_argument('datafile',
                            help="The datafile, in netCDF4 format, file.nc")

        return parser.parse_args(sys.argv[1:])

    args = parse_args()
    # print(args)

    JSdata = ERAJetStreamData(args.datafile)

    west, east, south, north = args.area
    if west == 0 and east == 0:
        west = min(JSdata.data['longitude'])
        east = max(JSdata.data['longitude'])
    if north == 0 and south == 0:
        south = min(JSdata.data['latitude'])
        north = max(JSdata.data['latitude'])
    print("WENS:", west, east, north, south)

    if args.listdata:
        print("In dataset %s:\n" % args.datafile)
        datadic = JSdata.list_data()
        for key in datadic:
            if type(datadic[key]) is str:
                print("%-10s: %s" % (key, datadic[key]))
            else:
                print("%s:" % key)
                for val in datadic[key]:
                    print("   ", val)
        sys.exit(0)

    if not args.outdir:
        args.outdir = 'outdir-%d-%s' % (args.level, args.threshold)
    if not os.path.exists(args.outdir):
        os.mkdir(args.outdir)
    elif not  os.path.isdir(args.outdir):
        print("Can't create dir %s: there's a file by that name" % args.outdir)
        sys.exit(1)

    timeunits = JSdata.data['time'].units
    cal = JSdata.data['time'].calendar
    for i, t in enumerate(JSdata.data['time']):
        thedate = netCDF4.num2date(t, units=timeunits, calendar=cal)
        timestr = thedate.strftime("%Y-%m-%d")

        JSdata.calc_windspeed(i, args.level, args.threshold)

        mymap = JSdata.create_map(args.level, timestr,
                                  west, east, south, north)

        figname = '%s/%s-%d.png' % (args.outdir, timestr, args.level)
        mymap.fig.savefig(figname, dpi=args.dpi)
        print(figname)
        plt.close()

