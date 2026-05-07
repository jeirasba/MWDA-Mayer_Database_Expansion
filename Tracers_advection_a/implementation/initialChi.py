#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: amayer02

Function for initialization of the tracer field.
In the current version of the code which implements equation (18) from Mayer and Wirth (2023)
the tracer field is initialized with zeros, independent on the tracer used.

"""

import xarray as xr
from config import wind

def initialize_with_zeros():
    '''Initialize the tracer field with zeros.'''
    
    # create a new xarray of zeros with the same shape and type as the wind field
    chi0 = xr.zeros_like(wind['u'][0])

    # set name and time
    chi0.name = 'chi0'
    chi0['time'] = wind.time[0]

    return chi0


