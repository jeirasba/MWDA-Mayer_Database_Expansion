#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Amelie Mayer

Specify the input data.
These configurations are then used in ../implementation/config.py to the set up the base (grid, input files, etc.) for the advection algorithm.

**********************************************************************************************
BEFORE RUNNING main_ERA5_lamda.py, adapt this file to specify the input path of the data, etc.
**********************************************************************************************

VARIABLES TO SPECIFY:
    path_of_data (str)              - the parent path to the input data 
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
    delta_timestep_of_data (int)    - the temporal resolution of the data (in hours) that shall be used 
    level1 (int)                    - the upper (model)level that shall be taken
    level2 (int)                    - the lower (model)level that shall be taken
    gridtype (str)                  - for ERA5 data on modellevels choose 'modellevels'
    target_pressures (boolean)      - whether the output shall be interpolated to pressure levels, default: True  
    timesteps_used_per_hour (int)   - number of timesteps per hour (the numerical timestep) that shall be used; for a 1° horizontal grid resolution 10 timesteps per hour are necessary, for a 0.5° horizontal grid resolution at least 15 timesteps per hour are necessary 
    
"""

###############################################
########## DATA SPECIFICATION #################
###############################################

# choose one of the configurations from below 
# in Mayer and wirth (2024) the following specification was used:
specification = 'MWDA'

# to run the mini-example, choose the following specification: 
#specification = 'example'

##############################################
##############################################

# different specifications
if specification == '1deg_3hourly_2ndml':
    resolution_of_vertical = 2
    delta_timestep_of_data = 3

elif specification == '1deg_3hourly':
    resolution_of_vertical = 1
    delta_timestep_of_data = 3

elif specification == '1deg_1hourly':
    resolution_of_vertical = 1
    delta_timestep_of_data = 1

elif specification == '1deg_6hourly_3rdml':
    resolution_of_vertical = 3
    delta_timestep_of_data = 6

# variables valid for the specifications from above 
if specification == '1deg_3hourly_2ndml' or specification == '1deg_3hourly' or specification == '1deg_1hourly' or specification == '1deg_6hourly_3rdml':
    path_of_data = '/lustre/miifs01/project/m2_jgu-w2w/w2w/amayer02/DATA/ERA5/ERA5_modellevels/1x1/'
    files_of_u = 'YYYY/MM/mlYYYYMMDD_HH_1x1_u_v_t.nc'
    files_of_v = files_of_u
    files_of_w = 'YYYY/MM/edYYYYMMDD_HH_1x1_etadot.nc'
    files_of_omega = 'YYYY/MM/mlYYYYMMDD_HH_1x1_w.nc'
    files_of_temperature = files_of_u
    files_of_surface_pressure = 'YYYY/MM/BYYYYMMDD_HH_1x1_sp.nc'
    files_of_theta_clim = '1x1_temperature_on_pl/data_3hourly_theta/climatologies/split_into_days/HH/ERA5_2010-2022_Feb-Oct_theta_HH_ydaymean_smoothed31days_MM_DD.nc'
    files_of_temp_clim = '1x1_temperature_on_pl/data_3hourly_t/climatologies/split_into_days/HH/ERA5_2010-2022_Feb-Oct_t_HH_ydaymean_smoothed31days_MM_DD.nc'
    files_of_diabatic_heating = 'diabatic_heating_1x1_regridded/YYYY/ml_YYYY-MM-DD_235005_HH.nc'
    date_of_ref = '2016-08-31_18'
    resolution_of_lat = 1
    resolution_of_lon = 1
    level1 = 50
    level2 = 137
    gridtype = 'modellevels'
    target_pressures = True
    timesteps_used_per_hour = 10

# specification for running the example
if specification == 'example':
    import os
    path_of_data = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'exampledata'))
    resolution_of_vertical = 3
    delta_timestep_of_data = 3
    files_of_u = 'u_v_t_ed_B/YYYY/MM/mlYYYYMMDD_HH_1x1_u_v_t.nc'
    files_of_v = files_of_u
    files_of_w = 'u_v_t_ed_B/YYYY/MM/edYYYYMMDD_HH_1x1_etadot.nc'
    files_of_omega = ''
    files_of_temperature = files_of_u
    files_of_surface_pressure = 'u_v_t_ed_B/YYYY/MM/BYYYYMMDD_HH_1x1_sp.nc'
    files_of_theta_clim = 'theta_climatology/ERA5_2010-2022_Feb-Oct_theta_HH_ydaymean_smoothed31days_MM_DD.nc'
    files_of_temp_clim = ''
    files_of_diabatic_heating = ''
    date_of_ref = '2020-08-30_00'
    resolution_of_lat = 1
    resolution_of_lon = 1
    level1 = 50
    level2 = 137
    gridtype = 'modellevels'
    target_pressures = True
    timesteps_used_per_hour = 10

if specification == 'MWDA':
    import os    
    path_of_data = '/lustre/miifs01/project/m2_jgu-w2w/w2w/amayer02/DATA/ERA5/ERA5_modellevels/1x1/'
    files_of_u = 'YYYY/MM/mlYYYYMMDD_HH_1x1_u_v_t.nc'
    files_of_v = files_of_u
    files_of_w = 'YYYY/MM/edYYYYMMDD_HH_1x1_etadot.nc'
    files_of_omega = 'YYYY/MM/mlYYYYMMDD_HH_1x1_w.nc'
    files_of_temperature = files_of_u
    files_of_surface_pressure = 'YYYY/MM/BYYYYMMDD_HH_1x1_sp.nc'
    files_of_theta_clim = '1x1_temperature_on_pl/data_3hourly_theta/climatologies/split_into_days/HH/ERA5_2010-2022_Feb-Oct_theta_HH_ydaymean_smoothed31days_MM_DD.nc'
    files_of_temp_clim = '1x1_temperature_on_pl/data_3hourly_t/climatologies/split_into_days/HH/ERA5_2010-2022_Feb-Oct_t_HH_ydaymean_smoothed31days_MM_DD.nc'
    files_of_diabatic_heating = 'diabatic_heating_1x1_regridded/YYYY/ml_YYYY-MM-DD_235005_HH.nc'
    date_of_ref = '2016-08-31_18'
    resolution_of_lat = 1
    resolution_of_lon = 1
    level1 = 50
    level2 = 137
    gridtype = 'modellevels'
    target_pressures = True
    timesteps_used_per_hour = 10
