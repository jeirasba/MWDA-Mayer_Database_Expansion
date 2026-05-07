#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Amelie Mayer

Method for reading in the ERA5 data (winds, pressure, ...) for driving the tracer advection algorithm.

"""

import xarray as xr
import numpy as np
import datetime
import os
import time as tm
import spharm
import pressureOnMl
import multiprocessing
from config import path_data, files_u, files_v, files_w, files_omega, files_surface_pressure, files_temperature, files_temp_clim, files_theta_clim, files_diabatic_heating, resolution_vertical, delta_timestep_data, level, lat, lon, RSPHERE, target_levels_pressure

def get_ERA5_data_hourly(i, date_start, timesteps_per_hour, hour_start=0, variables=[]):
      
    print('get_ERA5_data_hourly')
   
    '''
    Method for reading in the ERA5 data. Multiprocessing is used to read the individual variables in parallel.
    
    INPUT:
    i (int)                     - timestep
    date_start (str)            - starting date of simulation in the form YYYY-MM-DD, e.g. '2016-09-01'
    timesteps_per_hour (int)    - the number of timesteps used per hour, e.g. 10 for a horizontal resolution of 1° x 1°
    hour_start (str)            - starting hour of simulation, default: 0
    variables (list of str)     - A list of variables which should be read in. 
    
    OUTPUT:
    data_now, data_later (dict) - Two dictionaries containing the desired data for the current timestep and the data for the next timestep as numpy arrays.
    
    '''
    
    def get_data_for_interpolation(date_and_time, delta_timestep_data, path_data, filenames, variable, return_dict,return_xarray=False, name_variable=''):
        ''' Reads in the data files.'''
        
        # get date of file to be opened
        date_and_time = date_and_time + datetime.timedelta(hours=delta_timestep_data)
        year = datetime.datetime.strftime(date_and_time, '%Y')
        month = datetime.datetime.strftime(date_and_time, '%m')
        day = datetime.datetime.strftime(date_and_time, '%d')
        hour = datetime.datetime.strftime(date_and_time, '%H')
        date = datetime.datetime.strftime(date_and_time, '%Y%m%d_%H')
        
        # in case the temperature climatology for 29th of February shall be read in, use the temperature climatology of 28th of February
        if month == '02' and day == '29':
            if name_variable == 'theta_clim' or name_variable == 'temp_clim' or name_variable == 'theta_clim_hourly':           
                date_and_time = date_and_time - datetime.timedelta(hours=24)
                day = datetime.datetime.strftime(date_and_time, '%d')
                date = datetime.datetime.strftime(date_and_time, '%Y%m%d_%H')

        # get filename
        filename= os.path.join(path_data, filenames.replace('YYYY',year).replace('MM',month).replace('DD',day).replace('HH',hour))

        # open data file
        #data = xr.open_dataset(filename).isel(time=0)[variable]
        #Replaced by J.Eiras
        data = xr.open_dataset(filename, engine="netcdf4").isel(time=0)[variable]
        
        # rename dimensions if necessary
        if 'lat' in data.dims:
            data = data.rename({'lat':'latitude'})
        if 'lon' in data.dims:
            data = data.rename({'lon':'longitude'})
        if 'lev' in data.dims:
            data = data.rename({'lev':'level'})
    
        # if necessary, reverse latitude axis so that it goes from 90 ... -90
        if data.latitude[0] < 0:
            data = data.sel(latitude=slice(None, None, -1))
        
        # select specific levels
        if 'level' in data.dims: 
            
            # data on pressure levels
            if name_variable == 'theta_clim' or name_variable == 'temp_clim' or name_variable == 'theta_clim_hourly':
                data = data[{'level':slice(None, None, resolution_vertical)}]
                p1 = target_levels_pressure.sel(level=level[0])
                p2 = target_levels_pressure.sel(level=level[-1])
                data = data.sel(level=slice(p1, p2))
            
            # data on modellevels
            else:
                data = data.sel(level=level)

        if return_xarray == True:
            return data
        
        # get the data
        values = data.values
        
        # in case a neme for renaming is provided, rename
        if name_variable != '':
            variable = name_variable

        # store the values in the return_dict
        return_dict[variable] = values
        
        return values
       
    # set some variables
    path = path_data
    minutes_per_timestep = 60 / timesteps_per_hour
    date_and_time = datetime.datetime.strptime(date_start + ' ' + str(hour_start), '%Y-%m-%d %H') + datetime.timedelta(minutes=int(i*minutes_per_timestep))
    date = datetime.datetime.strftime(date_and_time, '%Y-%m-%d')
    hour = int(datetime.datetime.strftime(date_and_time, '%H'))
    
    # print some information
    print(date)
    print(hour)
    
    # set up multithreading for reading in each variable in parallel
    manager = multiprocessing.Manager()
    data_now = manager.dict()
    data_later = manager.dict()
    jobs = []

    # read in the individual variables
    # for the current and the next timestep
    # variable wind
    if 'wind' in variables:

        # zonal wind
        # data for current timestep
        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, 0, path_data, files_u, 'u', data_now))
        jobs.append(p)
        p.start()

        # data for next timestep
        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, delta_timestep_data, path_data, files_u, 'u', data_later))
        jobs.append(p)
        p.start()
        
        # meridional wind
        # data for current timestep
        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, 0, path_data, files_v, 'v', data_now))
        jobs.append(p)
        p.start()
        
        # data for next timestep
        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, delta_timestep_data, path_data, files_v, 'v', data_later))
        jobs.append(p)
        p.start()

        # vertical wind (eta vertical velocity [1/s])
        # data for current timestep
        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, 0, path_data, files_w, 'etadot', data_now, False, 'w'))
        jobs.append(p)
        p.start()
        
        # data for next timestep
        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, delta_timestep_data, path_data, files_w, 'etadot', data_later, False, 'w'))
        jobs.append(p)
        p.start()

    # vertical velocity (pressure vertical velocity [Pa/s])
    if 'omega' in variables:        
        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, 0, path_data, files_omega, 'w', data_now, False, 'omega'))
        jobs.append(p)
        p.start()

        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, delta_timestep_data, path_data, files_omega, 'w', data_later, False, 'omega'))
        jobs.append(p)
        p.start()
        
    # pressure
    if 'p' in variables:
        
        def get_p(date_and_time, delta_timestep_data, path_data, filenames, return_dict_now, return_dict_later):
            ''' Method for reading in the surface pressure and interpolate it to modellevels.'''
            
            # read in surface pressure
            p_surf_now = get_data_for_interpolation(date_and_time, 0, path_data, files_surface_pressure,'sp', return_dict_now,return_xarray=True)
            p_surf_later = get_data_for_interpolation(date_and_time, delta_timestep_data, path_data, files_surface_pressure, 'sp', return_dict_later,return_xarray=True)
 
            # calculate the pressure on modellevels
            p_ml_now = pressureOnMl.p_at_modellevels(p_surf_now,rename={'nhym':'level'})
            p_ml_later = pressureOnMl.p_at_modellevels(p_surf_later,rename={'nhym':'level'})
        
            # select certain levels
            p_ml_now = p_ml_now.sel(level=level)
            p_ml_later = p_ml_later.sel(level=level)
        
            # store data in units of hPa         
            return_dict_now['p'] = (p_ml_now.values[:,:,:]) / 100
            return_dict_later['p'] = (p_ml_later.values[:,:,:]) / 100

        p = multiprocessing.Process(target=get_p, args=(date_and_time, delta_timestep_data, path_data, files_w, data_now, data_later))
        jobs.append(p)
        p.start()

    # temperature
    if 't' in variables:
        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, 0, path_data, files_temperature, 't', data_now))
        jobs.append(p)
        p.start()
        
        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, delta_timestep_data, path_data, files_temperature, 't', data_later))
        jobs.append(p)
        p.start()
    
    # climatological mean of potential temperature
    if 'theta_clim' in variables:
        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, 0, path_data, files_theta_clim, 'theta', data_now, False, 'theta_clim'))
        jobs.append(p)
        p.start()

        # dummy
        data_later = []
    
    # climatological mean of temperature
    if 'temp_clim' in variables:
        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, 0, path_data, files_temp_clim, 't', data_now, False, 'temp_clim'))
        jobs.append(p)
        p.start()

        # dummy
        data_later = []
    
    # diabatic heating rate
    if 'diab_heating' in variables:
        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, 0, path_data, files_diabatic_heating, 'mttpm', data_now))
        jobs.append(p)
        p.start()

        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, delta_timestep_data, path_data, files_diabatic_heating, 'mttpm', data_later))
        jobs.append(p)
        p.start()
    
    # temporal change of climatological mean of potential temperature
    if 'temporal_change_theta_clim' in variables:

        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, -delta_timestep_data, path_data, files_theta_clim, 'theta', data_now, False, 'theta_clim'))
        jobs.append(p)
        p.start()

        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, delta_timestep_data, path_data, files_theta_clim, 'theta', data_later, False, 'theta_clim'))
        jobs.append(p)
        p.start()

    # temporal change of climatological mean of temperature
    if 'temporal_change_temp_clim' in variables:

        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, -delta_timestep_data, path_data, files_temp_clim, 'temp', data_now, False, 'temp_clim'))
        jobs.append(p)
        p.start()

        p = multiprocessing.Process(target=get_data_for_interpolation, args=(date_and_time, delta_timestep_data, path_data, files_temp_clim, 'temp', data_later, False, 'temp_clim'))
        jobs.append(p)
        p.start()


    # join the different jobs
    for proc in jobs:
        proc.join()
   
    # add some further information
    data_now['date'] = date
    data_now['hour'] = hour
    
    return data_now, data_later

    
def interpolation_timestep(i, date_start, timesteps_per_hour):
    ''' Get the interpolation timestep.'''
    timesteps_per_timestep = timesteps_per_hour * delta_timestep_data
    
    return (i%timesteps_per_timestep) / timesteps_per_timestep

def interpolate_linearly(timestep1, timestep2, intermediate_timestep):
    '''Linear interpolation in time.'''
    t1 = tm.time()
    interpolated = timestep1 + (timestep2-timestep1) * intermediate_timestep
    t2 = tm.time()
       
    return interpolated

def interpolate_now_later(data_now, data_later, intermediate_timestep):
    '''For every variable, interpolate the data from the current timestep and the next timestep linearly in time. Make use of the methods interpolate_linearly() and interpolation_timestep().'''
    data = {}
    for var in data_later.keys():
        data[var] = interpolate_linearly(data_now[var], data_later[var], intermediate_timestep)

    data['date'] = data_now['date']
    data['hour'] = data_now['hour']

    return data

def get_wind_data_ERA5(i, date_start, timesteps_per_hour, hour_start=0, variables=[]):
    '''Returns the method for reading in the ERA5 data. At the moment, the get_ERA5_data_hourly() is the only method implemented. In case in the future the input files will differ from the current input files, a new method can be added here.'''
    
    return get_ERA5_data_hourly(i, date_start, timesteps_per_hour, hour_start=hour_start, variables=variables), get_ERA5_data_hourly.__name__

    

