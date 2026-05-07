#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Amelie Mayer

Store the tracer field in .nc-files.

"""

import numpy as np
import xarray as xr
import stratify
import os

from config import s,target_levels_pressure,path_data,files_u, files_v, files_w,files_surface_pressure,files_temperature,files_theta_clim,files_temp_clim,files_omega,delta_timestep_data,timesteps_per_hour
import time as tm


def output_integration(*, i, chi, chi_start, pres, date, hour, lamda, tracermode,
                       savepath='', further_attr_netcdf={}):
    '''
    Store the output of the tracer algorithm in netCDF-files, interpolate to pressure levels.
    
    INPUT:
    i (int)             - timestep
    chi (spharm object) - tracer field in spectral space to be stored
    chi_start (xarray)  - initial tracer field
    pres                - current pressure on modellevels
    date (str)          - valid date of tracer field
    hour (int)          - valid hour of tracer field
    lamda (float)       - the lamda value in [1/seconds] determining the strength of relaxation 
    tracermode (str)    - name of the tracer
    savepath (str)      - directory to store the output
    further_attr_netcdf - attributes to save in the netCDF file
    
    OUTPUT:
    nc-files of the tracer fields are written to the directory savepath.
    
    '''
    
    # transform chi from spectral to physical space, move vertical axis to end
    chi_interim = np.moveaxis(s.spectogrd(chi), -1, 0)
 
    # interpolate tracer field from modellevels to pressure levels and make xarray
    if target_levels_pressure is not None:
    
        chi_on_pl = stratify.interpolate(target_levels_pressure, pres, chi_interim, axis=0, interpolation='linear')
        chi_on_pl = xr.DataArray(np.expand_dims(chi_on_pl,axis=0),
                    coords={'time':[np.datetime64(date+'T'+str(hour).zfill(2))],
                            'level':np.round(target_levels_pressure,2).astype('float32'), 
                            'latitude':chi_start.latitude.astype('int16'), 
                            'longitude':chi_start.longitude.astype('int16')},
                    dims=['time','level', 'latitude', 'longitude'])
    else:
        # xarray on modellevels
        chi_on_ml = xr.DataArray(np.expand_dims(chi_interim,axis=0),
                    coords={'time':[np.datetime64(date+'T'+str(hour).zfill(2))],
                        'level':np.round(chi_start.level,2).astype('float32'), 
                        'latitude':chi_start.latitude.astype('int16'), 
                        'longitude':chi_start.longitude.astype('int16')},
                    dims=['time','level', 'latitude', 'longitude'])

    # store tracer field on pressure levels
    if target_levels_pressure is not None:       
        save_chi_to_netCDF(i=i, chi_on_level=chi_on_pl,
                               interp_mode='pl',
                               further_attr_netcdf=further_attr_netcdf,
                               date=date, hour=hour,
                               savepath=savepath,
                               tracermode=tracermode)
    
    # store tracer field on modellevels
    else:
        save_chi_to_netCDF(i=i, chi_on_level=chi_on_ml,
                               interp_mode='ml',
                               further_attr_netcdf=further_attr_netcdf,
                               date=date, hour=hour,
                               savepath=savepath,
                               tracermode=tracermode)

def get_encoding_parameters(tracer):
    '''Set the scale_factor and add_offset values to store the data efficiently.'''

    if tracer == 'horizontal_temp' or tracer == 'horizontal_theta' or tracer == 'vertical_temp' or tracer == 'vertical_theta' or tracer == 'diabatic_temp' or tracer == 'diabatic_theta':
        set_min_max = {'chi_pl' : {'min': -100, 'max': 100}}
        encoding = {'chi_pl': { "dtype": "int16", "scale_factor": 0.0030518509475997192, "add_offset": 0, "_FillValue": -32768 }}
        # data with and without encoding differ at maximum by +/-0.00152 K

    elif tracer == 'latitude':
        set_min_max = {'chi_pl' : {'min': -90, 'max': 90}}
        encoding = {'chi_pl': { "dtype": "int16", "scale_factor": 0.0027466658528397473, "add_offset": 0, "_FillValue": -32768 }}

    elif tracer == 'pressure':
        set_min_max = {'chi_pl' : {'min': -1000, 'max': 1000}}
        encoding = {'chi_pl': { "dtype": "int16", "scale_factor": 0.030518509475997192, "add_offset": 0, "_FillValue": -32768 }}

    else: 
        set_min_max = {}
        encoding = {}

    return set_min_max, encoding
        
def save_chi_to_netCDF(*, i, chi_on_level, interp_mode, date, hour, tracermode, further_attr_netcdf={}, savepath=''):
    
    '''Save tracer field into netCDF-file.'''
    
    # attributes to save in the nc-file
    global_attrs={'timestep':str(i),
                    'path input data':path_data,
                    'wind u files':files_u,
                    'wind v files':files_v,
                    'wind w files':files_w,
                    'wind omega files':files_omega,
                    'pressure surface files':files_surface_pressure,
                    'potential temperature climatology':files_theta_clim,
                    'temperature climatology':files_temp_clim,
                    'delta timestep of data (hours)':delta_timestep_data,
                    'timesteps per hour':timesteps_per_hour}
    
    # further attributes to save in the netCDF file
    global_attrs.update(further_attr_netcdf)
    
    # make a dataset from the data arrays
    dataset = xr.Dataset({'chi_pl':chi_on_level},
                                 attrs=global_attrs)
    # sort by longitudes
    dataset = dataset.sortby('longitude')

    # set an encoding to store netcdf-file with add_offset and scale_factor parameter
    set_min_max, encoding = get_encoding_parameters(tracermode)
    
    # if encoding/set_min_max is not empty, set min_max_values for encoding
    if not bool(set_min_max):
        for var in list(set_min_max.keys()):
            # set those values that are out of the covered range to the min/max value of the range
            dataset[var] = xr.where(dataset[var] > set_min_max[var]['max'], set_min_max[var]['max'], dataset[var])
            dataset[var] = xr.where(dataset[var] < set_min_max[var]['min'], set_min_max[var]['min'], dataset[var])

    # save dataset to netCDF
    dataset.to_netcdf(os.path.join(savepath,'chi_on_'+interp_mode+'_'+date+'_'+str(hour).zfill(2)+'_'+str(i).zfill(4)+'.nc'), encoding=encoding)    
