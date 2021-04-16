#!/usr/bin/env python3

"""Extract time series from Norkyst 800 m forecasts on MET THREDDS server (thredds.met.no) 

and do something (for now: print and plot) with them

Hourly resolution (from 2017-02-20T00:00): https://thredds.met.no/thredds/fou-hi/norkyst800v2.html
Dayily averages (from 2012-06-27T12:00): https://thredds.met.no/thredds/fou-hi/norkyst800m.html

Test: 
'python3 THREDDSImporter.py -lon 3 -lat 60 -depth 3 -param temperature -S 2021-04-14T00:00 -E 2021-04-15T00:00'

TODO:
 - Add support for -S and -E over multiple files (<-- MLS will fix this this evening!)
 - Tune processing and storing of observational data sets (to suite whatever code that will use the data sets)
 - (See TODOs in FrostImporter.py)
 - ...
"""

import argparse
import datetime
from traceback import format_exc
import netCDF4
import numpy as np
import pyproj as proj
import sys

import matplotlib.pyplot as plt

class THREDDSImporter:
    def __init__(self, frost_api_base=None, station_id=None, start_time=None, end_time=None):
        lon, lat, depth, params, start_time, end_time = self.__parse_args()
 
        filenames = ["https://thredds.met.no/thredds/dodsC/fou-hi/norkyst800m-1h/NorKyst-800m_ZDEPTHS_his.an.2021041500.nc",
                    "https://thredds.met.no/thredds/dodsC/fou-hi/norkyst800m-1h/NorKyst-800m_ZDEPTHS_his.an.2021041400.nc",
                    "https://thredds.met.no/thredds/dodsC/fou-hi/norkyst800m-1h/NorKyst-800m_ZDEPTHS_his.an.2021041300.nc",
                    "https://thredds.met.no/thredds/dodsC/fou-hi/norkyst800m-1h/NorKyst-800m_ZDEPTHS_his.an.2021041300.nc",
                    "https://thredds.met.no/thredds/dodsC/fou-hi/norkyst800m-1h/NorKyst-800m_ZDEPTHS_his.an.2021041200.nc",
                    "https://thredds.met.no/thredds/dodsC/fou-hi/norkyst800m-1h/NorKyst-800m_ZDEPTHS_his.an.2021041100.nc"]

        data = {}
        for param in params:
            data[param] = self.__norkyst_from_thredds(filenames, param, lon, lat, depth)

        # plots first param
        fig = plt.figure()
        plt.plot(data[params[0]])
        plt.show()

    def __norkyst_from_thredds(self, filenames, param, lon, lat, depth=None):
        nc  = netCDF4.MFDataset(filenames)

        # handle projection
        for var in ['polar_stereographic','projection_stere','grid_mapping']:
            if var in nc.variables.keys():
                try:
                    proj1 = nc.variables[var].proj4
                except:
                    proj1 = nc.variables[var].proj4string
        p1 = proj.Proj(str(proj1))
        xp1,yp1 = p1(lon,lat)
        for var in ['latitude','lat']:
            if var in nc.variables.keys():
                lat1 = nc.variables[var][:]
        for var in ['longitude','lon']:
            if var in nc.variables.keys():
                lon1 = nc.variables[var][:]
        xproj1,yproj1 = p1(lon1,lat1)

        # find coordinate of gridpoint to analyze
        x1=self.__find_nearest_index(xproj1[0,:],xp1)
        y1=self.__find_nearest_index(yproj1[:,0],yp1)
        print('Coordinates model1 (x,y= '+str(x1)+','+str(y1)+'): '+str(lat1[y1,x1])+', '+str(lon1[y1,x1]))

        if depth is not None:
            # find correct depth index
            all_depths = nc.variables["depth"][:]
            depth_index = np.where(all_depths == int(depth))[0][0]
            
            return nc.variables[param][depth_index,:,y1,x1]
        else:
            return nc.variables[param][:,y1,x1]

    @staticmethod
    def __find_nearest_index(array,value):
        idx = (np.abs(array-value)).argmin()
        return idx

    @staticmethod
    def __parse_args():
        parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
            '-lon', dest='lon', required=True,
            help='fetch data for grid point nearest to given longitude coordinate')
        parser.add_argument(
            '-lat', dest='lat', required=True,
            help='fetch data for grid point nearest to given latitude coordinate')
        parser.add_argument(
            '-depth', dest='depth', required=False,
            choices=['0', '3', '10', '15', '25', '50', '75', '100', '150', '200', '250', '300', '500', '1000', '2000', '3000'],
            help='fetch data for given depth in meters')
        parser.add_argument(
            '-param', required=True, action='append',
            help='fetch data for parameter')
        parser.add_argument(
            '-S', '--start-time', required=True,
            help='start time in ISO format (YYYY-MM-DDTHH:MM) UTC')
        parser.add_argument(
            '-E', '--end-time', required=True,
            help='end time in ISO format (YYYY-MM-DDTHH:MM) UTC')
        res = parser.parse_args(sys.argv[1:])
        return res.lon, res.lat, res.depth, res.param, res.start_time, res.end_time

if __name__ == "__main__":

    try:
        THREDDSImporter()
    except SystemExit as e:
        if e.code != 0:
            print('SystemExit(code={}): {}'.format(e.code, format_exc()), file=sys.stderr)
            sys.exit(e.code)
    except: # pylint: disable=bare-except
        print('error: {}'.format(format_exc()), file=sys.stderr)
        sys.exit(1)

    sys.exit(0)
