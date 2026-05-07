#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Amelie Mayer

Functions used for the configuration of the setup (grid) the advection algorithm works on.

"""

import xarray as xr
import numpy as np
import os

def get_grid_modellevels(absolute_path_data, level1=1, level2=137, resolution_lat=1, resolution_lon=1, resolution_vertical=1):
    '''Return reference xarray to establish grid (modellevels).
    
    INPUT:
    absolute_path_data (str)    - the absolute path of the data file which should be used to infer the latitude-longitude-height grid from
    level1 (int)                - upper modellevel that should be used
    level2 (int)                - lower modellevel that should be used
    resolution_lat (int)        - choose 1 for using every latitude given in the reference file, choose 2 for only using every second latitude, etc.
    resolution_lon (int)        - choose 1 for using every longitude given in the rference file, choose 2 for only using every second longitude, etc.
    resolution_vertical (int)   - choose 1 for using every vertical level given in the file, choose 2 for only using every second vertical level, etc.
    
    OUTPUT:
    wind - returns (some arbitrary) xarray on the desired latitude-longitude-height grid
    
    '''
    
    print('File for configuration: ' + absolute_path_data)
    
    # open reference data file
    print(absolute_path_data)
    wind = xr.open_dataset(absolute_path_data)
    
    # rename dimensions if necessary
    if 'lat' in wind.dims:
        wind = wind.rename({'lat':'latitude'})
    if 'lon' in wind.dims:
        wind = wind.rename({'lon':'longitude'})
    if 'lev' in wind.dims:
        wind = wind.rename({'lev':'level'})
    
    # if necessary, reverse latitude axis so that it goes from 90 ... -90
    if wind.latitude[0] < 0:
        wind = wind.sel(latitude=slice(None, None, -1))

    # only take every xth latitude, longitude, level
    wind = wind[{'level':slice(None, None, resolution_vertical)}] 
    wind = wind[{'latitude':slice(None, None, resolution_lat)}] 
    wind = wind[{'longitude':slice(None, None, resolution_lon)}] 
    
    # only take modellevels from level1 to level2
    wind = wind.sel(level=slice(level1, level2))
    
    # change longitudes from 0..360 to -180..180
    wind = wind.assign_coords(longitude=(((wind.longitude + 180) % 360) - 180))
      
    return wind

def get_grid(gridtype, absolute_path_data, level1=0,level2=137, resolution_lat=1, resolution_lon=1, resolution_vertical=1):
    ''' Returns a reference xarray to establish the respective grid corresponding to the gridtype. At the moment, the get_grid_modellevels() is the only method implemented.'''
    
    if gridtype == 'modellevels':
        reference_xarray = get_grid_modellevels(absolute_path_data, level1=level1, level2=level2, resolution_lat=resolution_lat, resolution_lon=resolution_lon, resolution_vertical=resolution_vertical)
    return reference_xarray
    

def get_target_levels_pressure(modellevels):
    '''Calculate the reference pressure levels onto which the data on modellevels shall be interpolated to.
    Pressure levels are calculated from surface pressure and the modellevel coefficients.
    A surface pressure of 1013.25 hPa is used to infer the target pressure levels.'''
    
    # get modellevel coefficients
    path = os.path.abspath(__file__)
    dir_path = os.path.dirname(path)
    coeff = xr.open_dataset(os.path.join(dir_path,'coefficients_ERA5.nc'))
    
    # make target pressure levels
    # rename vertical axis, only choose those modellevels which are present in input data
    target_levels_pressure = coeff['hyam'] + coeff['hybm'] * 101325
    target_levels_pressure = target_levels_pressure.rename({'nhym':'lev'})
    target_levels_pressure = target_levels_pressure.sel(lev=modellevels)
    
    # return pressure levels in unit of hPa
    return target_levels_pressure / 100
    
def get_eta_values(lat, lon, levels):
    '''Get the values of the eta vertical coordinate and return its difference between two consecutive vertical levels.
    The value of the eta vertical coordinate is calculated from a reference surface pressure (1013.25 hPa) and the modellevel coefficients.'''
    
    # get modellevel coefficients
    path = os.path.abspath(__file__)
    dir_path = os.path.dirname(path)
    coeff = xr.open_dataset(os.path.join(dir_path,'coefficients_ERA5.nc'))
    
    # calculate the value of eta
    eta = coeff['hyam'] / 101325 + coeff['hybm']
    
    # rename vertical axis, only choose those modellevels corresponding to "levels"
    eta = eta.rename({'nhym':'lev'})
    eta = eta.sel(lev=levels)
        
    # compute centered differences of eta 
    delta_eta = np.gradient(eta)

    # make a meshgrid of the delta_eta values
    _,_,Delta_eta = np.meshgrid(lat, lon, delta_eta, indexing='ij')
    
    return Delta_eta


