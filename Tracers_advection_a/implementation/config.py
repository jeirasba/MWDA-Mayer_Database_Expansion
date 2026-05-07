#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Amelie Mayer

Configuration of the set up (grid, input files, etc.) for the advection algorithm.
Here, global variables are set, which are used in model.py, initialChi.py, output.py, windsERA5.py, and the mainfunction.
The variables given to the config-method are set in ../mainfunctions/myconfigs.py and imported from there.

"""

import getData
import numpy as np
import spharm
import os
import sys
import datetime
sys.path.append('..')
sys.path.append('../mainfunctions')

from myconfigs import path_of_data, delta_timestep_of_data, timesteps_used_per_hour, gridtype, target_pressures, files_of_u, files_of_v, files_of_w, files_of_omega, files_of_surface_pressure, files_of_temperature, files_of_temp_clim, files_of_theta_clim, files_of_diabatic_heating, date_of_ref, resolution_of_vertical, resolution_of_lat, resolution_of_lon, level1, level2


def config():
    '''
    Set up global variables (like latitudes, longitudes, etc.) for advection algorithm.
    The function uses those variables which are imported from myconfig.py.
    
    INPUT:
    path_of_data (str)              - the parent path to the input data
    delta_timestep_of_data (int)    - the temporal resolution of the data (in hours) that shall be used 
    timesteps_used_per_hour (int)   - number of timesteps per hour (the numerical timestep) that shall be used; for a 1° horizontal grid resolution 10 timesteps per hour are necessary, for a 0.5° horizontal grid resolution at least 15 timesteps per hour are necessary 
    gridtype (str)                  - for ERA5 data on modellevels choose 'modellevels'
    target_pressures (boolean)      - whether the output shall be interpolated to pressure levels, default: True 
    files_of_u (str)                - the child path and filename of input files of zonal wind, with placeholder YYYY, MM, DD, HH for the datetime
    files_of_v (str)                - the child path and filename of input files of meridional wind, with placeholder YYYY, MM, DD, HH for the datetime
    files_of_w (str)                - the child path and filename of input files of vertical wind (eta vertical velocity), with placeholder YYYY, MM, DD, HH for the datetime
    files_of_omega (str)            - the child path and filename of input files of vertical wind (pressure vertical velocity), with placeholder YYYY, MM, DD, HH for the datetime
    files_of_surface_pressure (str) - the child path and filename of input surface pressure files, with placeholder YYYY, MM, DD, HH for the datetime
    files_of_temperature (str)      - the child path and filename of input temperature files, with placeholder YYYY, MM, DD, HH for the datetime
    files_of_temp_clim (str)        - the child path and filename of input climatological temperature files, with placeholder YYYY, MM, DD, HH for the datetime
    files_of_theta_clim (str)       - the child path and filename of input climatological potential temperature files, with placeholder YYYY, MM, DD, HH for the datetime
    files_of_diabatic_heating (str) - the child path and filename of input diabatic heating rates, with placeholder YYYY, MM, DD, HH for the datetime
    date_of_ref (str)               - one (arbitrary) datetime for which data in path_of_data are available, must contain YYYY, MM, DD, HH as placeholder 
    resolution_of_vertical (int)    - the vertical resolution; "1" to take each vertical level present in the input data, "2" to take every second vertical level present in the input data, etc.
    resolution_of_lat (int)         - the resolution in the meridional direction; "1" to take each latitude present in the input data, "2" to take every second latitude present in the input data, etc.
    resolution_of_lon (int)         - the resolution in the zonal direction; "1" to take each longitude present in the input data, "2" to take every second longitude present in the input data, etc.
    level1 (int)                    - the upper (model)level that shall be taken
    level2 (int)                    - the lower (model)level that shall be taken
    
    '''
    
    # all global variables
    global lon
    global lat
    global level
    global delta_lon
    global delta_lat
    global delta_level
    global delta_timestep_data
    global timesteps_per_hour
    global Pressure
    global RSPHERE 
    global NLAT   
    global s 
    global wind
    global path_data
    global files_u
    global files_v
    global files_w
    global files_omega
    global files_surface_pressure
    global files_temperature
    global files_temp_clim
    global files_theta_clim
    global files_diabatic_heating
    global target_levels_pressure
    global target_levels_height
    global Lat
    global Lon
    global Level
    global Delta_eta
    global resolution_vertical
    global resolution_lat
    global resolution_lon
    
    # set some of these global variables
    path_data = path_of_data
    delta_timestep_data = delta_timestep_of_data
    timesteps_per_hour = timesteps_used_per_hour
    files_u = files_of_u
    files_v = files_of_v
    files_w = files_of_w
    files_omega = files_of_omega
    files_surface_pressure = files_of_surface_pressure
    files_temperature = files_of_temperature
    files_temp_clim = files_of_temp_clim
    files_theta_clim = files_of_theta_clim
    files_diabatic_heating = files_of_diabatic_heating
    ref_date = date_of_ref
    resolution_vertical = resolution_of_vertical
    resolution_lat = resolution_of_lat
    resolution_lon = resolution_of_lon
    
    # get year, month, day, hour of reference date
    date_ref_as_datetime = datetime.datetime.strptime(ref_date, '%Y-%m-%d_%H')
    year = datetime.datetime.strftime(date_ref_as_datetime, '%Y')
    month = datetime.datetime.strftime(date_ref_as_datetime, '%m')
    day = datetime.datetime.strftime(date_ref_as_datetime, '%d')
    hour = datetime.datetime.strftime(date_ref_as_datetime, '%H')
    
    # build the string of the reference file
    reference_file = os.path.join(path_of_data, files_u.replace('YYYY', year).replace('MM', month).replace('DD', day).replace('HH', hour))
       
    # initialize grid
    wind = getData.get_grid(gridtype, 
                            reference_file,
                            level1=level1, level2=level2, resolution_lat=resolution_lat, resolution_lon=resolution_lon,
                            resolution_vertical=resolution_vertical)
    
    # set the target levels for interpolation onto vertical grid
    # interpolate to pressure levels (default) 
    if target_pressures == True:
        target_levels_pressure = getData.get_target_levels_pressure(wind.level)
    else:
        target_levels_pressure = None 
    
    # get and set grid specific values
    lon = wind.longitude.values         
    lat = wind.latitude.values         
    level = wind.level.values
    delta_lon = np.diff(lon)[0]
    delta_lat = np.diff(lat)[0]
    delta_level = int(np.diff(level)[0])
    Delta_eta = getData.get_eta_values(lat, lon, level)
    Pressure = np.meshgrid(level, lat, lon, indexing='ij')[0]  
    RSPHERE = 6371229
    NLAT = len(lat)
    
    # set up a meshgrid
    Level,Lat,Lon = np.meshgrid(level, lat, lon, indexing='ij')
    
    # set up the spharm object to convert data to spectral space
    s = spharm.Spharmt(len(lon), len(lat), rsphere=RSPHERE, legfunc='stored', gridtype='regular')
      
# call the config-method to configure the set up by setting global variables
# the variables used in the config-method are imported from ../mainfunctions/myconfigs.py
config()
