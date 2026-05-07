#!/usr/bin/env python3
"""
@author: Amelie Mayer

Method for calculating pressure on modellevels from surface pressure and ERA5 modellevel coefficients. 

"""

import xarray as xr
import os
import sys
import numpy as np

def p_at_modellevels(surface_pressure,rename={'nhym':'level','sp':'p'}):
    '''Calculate pressure on modellevels from surface pressure files.
    
    INPUT:
    surface pressure (xarray) - surface pressure
    
    RETURN:
    p_at_modellevels (xarray) - pressure on modellevels
    
    '''
    
    # get modellevel coefficients
    path = os.path.abspath(__file__)
    dir_path = os.path.dirname(path)
    coefficients = xr.open_dataset(os.path.join(dir_path,'coefficients_ERA5.nc'))
   
    # calculate pressure on modellevels from surface pressure    
    p_at_modellevels = coefficients['hyam'] + coefficients['hybm'] * surface_pressure
    p_at_modellevels = p_at_modellevels.rename(rename)
    
    # rename dimensions if necessary
    if 'lat' in p_at_modellevels.dims:
        p_at_modellevels = p_at_modellevels.rename({'lat':'latitude'})
    if 'lon' in p_at_modellevels.dims:
        p_at_modellevels = p_at_modellevels.rename({'lon':'longitude'})
    if 'lev' in p_at_modellevels.dims:
        p_at_modellevels = p_at_modellevels.rename({'lev':'level'})
     
    # order dimensions like in wind files
    if 'time' in p_at_modellevels.dims:
        p_at_modellevels = p_at_modellevels.transpose('time','level','latitude','longitude')
    else:
        p_at_modellevels = p_at_modellevels.transpose('level','latitude','longitude')
    
    return p_at_modellevels
