#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Amelie Mayer

The central part of the code: The integration method/algorithm to solve the advection-relaxation equation on the 3D globe.
As time scheme the third order Runge Kutta scheme of Williamson is used.
A pseudo-spectral method is applied to overcome the pole problem. Therefore, the integration is done in spectral space. 
Horizontal and vertical gradients as well as the advection term are determined in physical space and then transformed to spectral space. 
So is the source term.
The relaxation term is directly determined in spectral space.

"""

import numpy as np
import spharm
import time as tm
from scipy.interpolate import interpn
import output
import windsERA5
import xarray as xr

from config import delta_lon, delta_lat, delta_level,Delta_eta,RSPHERE,NLAT,s,Lat,Lon, delta_timestep_data, lat, lon, level, target_levels_pressure   

def integration(*, chi_start, wind, delta_t, lamda, timesteps, tracermode=None,
                args_wind=[], kwargs_wind={},
                output_frequency=50,
                savepath=''):
    
    '''The integration method of the tracer advection algorithm on the 3D globe.
    
    INPUT:
    chi_start (xarray)          - initial tracer field
    wind (a function)           - the wind function to get the 3D wind field
    delta_t (int)               - the timestep in [seconds]
    lamda (float)               - the lamda value in [1/seconds] determining the strength of relaxation
    timesteps (int)             - the number of total timesteps to be perfomrmed
    tracermode (str)            - the name of the tracer
    args_wind (dict)            - args for wind function
    kwargs_wind (dict)          - kwargs for wind function
    output_frequency (int)      - the output frequency in terms of timesteps
    savepath (str)              - directory to store the output
    
    RETURN:
    chi_final (xarray) - the tracer field after the full amount of timesteps
    
    OUTPUT:
    nc-files of the intermediate tracer fields are written to the directory savepath.
    
    '''

    # to get final result stored, too
    timesteps = timesteps + output_frequency
    
    # move vertical axis to end, transform chi_start from xarray to numpy array
    chi0 = np.moveaxis(chi_start.values, 0, -1)
    
    # transform chi0 from physical space to spectral space
    chi = s.grdtospec(chi0)

    # now, integrate chi for every timestep 
    for i in np.arange(0, timesteps+1):
        
        # get the data
        if windsERA5.interpolation_timestep(i, *args_wind) == 0.0:
            
            # if needed, read in new files ...
            [data_now, data_later], used_wind_fct = wind(i, *args_wind, **kwargs_wind)
            data = data_now
            
            # if needed, read in the temperature climatology specific to the tracermode
            if tracermode == 'horizontal_theta' or tracermode == 'vertical_theta':
                [t_clim_now, dummy], used_wind_fct = wind(i, *args_wind, **{**kwargs_wind, 'variables': ['theta_clim']})
                t_clim_on_pres = t_clim_now['theta_clim']
            elif tracermode == 'horizontal_temp' or tracermode == 'vertical_temp':
                [t_clim_now, dummy], used_wind_fct = wind(i, *args_wind, **{**kwargs_wind, 'variables': ['temp_clim']})
                t_clim_on_pres = t_clim_now['temp_clim']
            else:
                t_clim_on_pres = []

            # ... here maybe some problems will arise if resolution is hourly instead of a multiple of 3 ... care about this later ...
            
            # if tracermode seasonality is used, read in climatological temperature for two timesteps to compute temporal change
            if tracermode == 'seasonality_theta':
                # get temperature climatology for the previous and the subsequent timestep
                [t_clim_earlier, t_clim_later], used_wind_fct = wind(i, *args_wind, **{**kwargs_wind, 'variables': ['temporal_change_theta_clim']})
                # from that compute temporal change in temperature climatology as centered differences
                temporal_change_t_clim_on_pres = (t_clim_later['theta_clim'] - t_clim_earlier['theta_clim']) / (2 * delta_timestep_data * 60 * 60)
                # interpolate to modellevels
                temporal_change_t_clim_on_ml = interpolate_variable_to_ml(data['p'], temporal_change_t_clim_on_pres)
            elif tracermode == 'seasonality_temp':
                # get temperature climatology for the previous and the subsequent timestep
                [t_clim_earlier, t_clim_later], used_wind_fct = wind(i, *args_wind, **{**kwargs_wind, 'variables': ['temporal_change_temp_clim']})
                # from that compute temporal change in temeraure climatology as centered differences
                temporal_change_t_clim_on_pres = (t_clim_later['temp_clim'] - t_clim_earlier['temp_clim']) / (2 * delta_timestep_data * 60 * 60)
                # interpolate to modellevels
                temporal_change_t_clim_on_ml = interpolate_variable_to_ml(data['p'], temporal_change_t_clim_on_pres)
            else:
                temporal_change_t_clim_on_ml = []

            # from the temperature climatology, get the temperature gradient on modellevels where needed
            grad_t_clim_on_ml_u = []
            grad_t_clim_on_ml_v = []
            grad_t_clim_on_ml_w = []
            if tracermode == 'vertical_temp' or tracermode == 'vertical_theta':
                grad_t_clim_on_ml_w = get_climatological_temperature_gradients_on_ml(data['p'], t_clim_on_pres, tracermode)
            elif tracermode == 'horizontal_temp' or tracermode == 'horizontal_theta':
                grad_t_clim_on_ml_u, grad_t_clim_on_ml_v = get_climatological_temperature_gradients_on_ml(data['p'], t_clim_on_pres, tracermode)

        else:        
            # or just interpolate the data to the specific timestep ...
            data = windsERA5.interpolate_now_later(data_now, data_later, windsERA5.interpolation_timestep(i, *args_wind))

        # allocate some variables
        u = data['u']     # zonal component of wind field
        v = data['v']     # meriodional component of wind field        
        w = data['w']     # vertical component of wind field
                 
        if 't' in data.keys():
            temp = data['t']    # temperature
        else:
            temp = []

        if 'p' in data.keys():
            pres = data['p']    # pressure
        else:
            pres = []

        if 'omega' in data.keys():
            omega = data['omega']   # omega
        else:
            omega = []

        if 'mttpm' in data.keys():
            diab_heat = data['mttpm']   # diabatic heating
        else:
            diab_heat = []
    
        # set date and hour
        date = data['date']
        hour = data['hour']

        # get the strength of the additional hyperdiffusion depending on horizontal resolution
        horizontal_resolution = max(delta_lat, delta_lon)
        diffusion_kappa = get_diffusion_kappa(horizontal_resolution)

        # store output
        if i % output_frequency == 0:
            output.output_integration(i=i, chi=chi, chi_start=chi_start, pres=pres,
                                      date=date, hour=hour,
                                      lamda=lamda, 
                                      tracermode=tracermode,
                                      savepath=savepath,
                                      further_attr_netcdf={'used_wind_fct':used_wind_fct,'lamda':lamda, 'kappa':diffusion_kappa})
        
        # start clocking to check how long the integration takes
        t1 = tm.time()
        print('timestep ' + str(i))

        # do the integration step
        chi = integrationstep_with_hyperdiffusion(chi=chi, delta_t=delta_t,
                                                  u=u, v=v, w=w, omega=omega,
                                                  lamda=lamda, 
                                                  pres=pres, temp=temp,
                                                  diab_heat=diab_heat,
                                                  grad_t_clim_on_ml_u = grad_t_clim_on_ml_u,
                                                  grad_t_clim_on_ml_v = grad_t_clim_on_ml_v,
                                                  grad_t_clim_on_ml_w = grad_t_clim_on_ml_w,
                                                  temporal_change_t_clim_on_ml = temporal_change_t_clim_on_ml,
                                                  diffusion_kappa=diffusion_kappa,
                                                  tracermode=tracermode, i=i)

        # stop clocking to check how long the integration takes
        t2 = tm.time()
        print("--- %s seconds for integration step ---" % (t2 - t1) + '\n')
    
    # transform the final tracer field from spectral space to physical space, move vertical axis to front
    chi_final = np.moveaxis(s.spectogrd(chi), -1, 0)
                    
    return chi_final

def get_diffusion_kappa(horizontal_resolution):
    '''Get the strength of the additional hyperdiffusion depending on the horizontal resolution.'''
    
    # in case of 1° x 1° horizontal grid
    if horizontal_resolution == 1:
        diffusion_kappa = 3E14
    
    # in case of 0.5° x 0.5° horizontal grid
    elif horizontal_resolution == 0.5:
        diffusion_kappa=3E13

    # in case of 2° x 2° horizontal grid
    elif horizontal_resolution == 2:
        diffusion_kappa=3E15

    else:
        raise Exception('For this '+str(horizontal_resolution)+' no kappa_value has been chosen yet.')
    
    return diffusion_kappa

def laplacian_eigenvalues(ntrunc, n_levels):
    '''Get the Laplacian eigenvalues.'''
    _,specindx = spharm.getspecindx(ntrunc)
    laplacian_eigenvalues = (specindx * (1. + specindx) / RSPHERE / RSPHERE).astype(np.complex64, casting="same_kind")

    # change 1d array into 2d array of shape (16471,10)
    laplacian_eigenvalues = np.moveaxis(np.tile(laplacian_eigenvalues, (n_levels,1)),0,-1)
    
    return laplacian_eigenvalues

def get_horizontal_gradients(chi):
    '''Get the horizontal gradients of chi in physical space from chi in spectral space.
    
    INPUT:
    chi (spharm object) - the tracer field in spectral space
    
    RETURN:
    grad_u (numpy array)    - zonal gradient of chi in physical space
    grad_v (numpy array)    - meridional gradient of chi in physical space
    '''
    
    grad_u, grad_v = s.getgrad(chi)

    return grad_u, grad_v


def integrationstep_with_hyperdiffusion(*, chi, delta_t, u, v, w, omega, lamda, pres, temp, diab_heat, grad_t_clim_on_ml_u, grad_t_clim_on_ml_v, grad_t_clim_on_ml_w, temporal_change_t_clim_on_ml, diffusion_kappa, tracermode, i):
    '''Do the integrationstep in spectral space. Additional hyperdiffusion is applied to stabilize algorithm. As time scheme the third order Runge Kutta scheme of Williamson is used.
    The variables omega, pres, temp, diab_heat, grad_t_clim_on_ml_u, grad_t_clim_on_ml_v, grad_t_clim_on_ml_w, temporal_change_t_clim_on_ml are given to compute the respective source term.
    Depending on the tracer mode, data (numpy arrays) is only assigned to certain of these variables.
    
    INPUT:
    chi (spham object)                                      - the tracer field in spectral space
    delta_t (int)                                           - the timestep in [seconds]
    u, v, w (numpy array)                                   - the zonal, meridional, and vertical wind in physical space
    omega (numpy array/empty list)                          - vertical wind in pressure coordinates provided as a numpy array; if not needed empty list
    lamda (float)                                           - the lamda value in [1/seconds] determining the strength of relaxation to environment 
    pres (numpy array/empty list)                           - pressure provided as a numpy array; if not needed empty list                            -
    temp (numpy array/empty list)                           - temperature provided as a numpy array; if not needed empty list
    diab_heat (numpy array/empty list)                      - diabatic heating rate provided as a numpy array; if not needed empty list
    grad_t_clim_on_ml_u (numpy array/empty list)            - climatological zonal temperature gradient on modellevels provided as a numpy array; if not needed empty list
    grad_t_clim_on_ml_v (numpy array/empty list)            - climatological meridional temperature gradient on modellevels provided as a numpy array; if not needed empty list
    grad_t_clim_on_ml_w (numpy array/empty list)            - climatological vertical temperature gradient on modellevels provided as a numpy array; if not needed empty list
    temporal_change_t_clim_on_ml (numpy array/empty list)   - temporal change of climatological temperature on modellevels provided as a numpy array; if not needed empty list
    diffusion_kappa (int)                                   - strength of the additional hyperdiffusion
    tracermode (str)                                        - the name of the tracer


    RETURN:
    chi (spharm object) - the tracer field in spectral space after one integration step
    
    '''
       
    # for hyperdiffusion
    ntrunc = NLAT - 1
    diffusion_order = 2
    eigenvalues_exp = laplacian_eigenvalues(ntrunc, len(chi[0,:])) ** diffusion_order

    # get the source term
    source_term = source(u=u, v=v, w=w, omega=omega, grad_t_clim_on_ml_u=grad_t_clim_on_ml_u, grad_t_clim_on_ml_v=grad_t_clim_on_ml_v, grad_t_clim_on_ml_w=grad_t_clim_on_ml_w, temporal_change_t_clim_on_ml=temporal_change_t_clim_on_ml, pres=pres, temp=temp, diab_heat=diab_heat, tracermode=tracermode)
    
    # third order Runge Kutta time scheme of Williamson 
    k = delta_t * tendency_chi(chi=chi, u=u, v=v, w=w, lamda=lamda, source_term=source_term)
    chi = chi + (1/3.) * k
    
    k = delta_t * tendency_chi(chi=chi, u=u, v=v, w=w, lamda=lamda, source_term=source_term) - (5/9.) * k
    chi = chi + (15/16.) * k
    
    k = delta_t * tendency_chi(chi=chi, u=u, v=v, w=w, lamda=lamda, source_term=source_term) - (153/128.) * k
    chi = chi + (8/15.) * k
    
    # add hyperdiffusion
    chi = chi / (1 + (delta_t * diffusion_kappa * eigenvalues_exp))
       
    return chi

def tendency_chi(*, chi, u, v, w, lamda, source_term):
    '''Right side of advection-relaxation equation, i.e. the approximated tendency delta_chi/delta_t.
    
    INPUT:
    chi (spham object)              - the tracer field in spectral space
    u, v, w (numpy array)           - the zonal, meridional, and vertical wind in physical space
    lamda (float)                   - the lamda value in [1/seconds] determining the strength of relaxation to environment 
    source_term (spharm object)     - the approximated tendency delta_chi/delta_t tracer due to the source term
    
    RETURN:
    chi (spharm object) - the approximated tendency delta_chi/delta_t 
    
    '''

    chi = -advection(chi=chi, u=u, v=v, w=w) - relaxation(chi=chi, lamda=lamda) - source_term
    
    return chi

def relaxation(*, chi, lamda):
    '''The approximated tendency delta_chi/delta_t due to relaxation.
    
    INPUT:
    chi (spham object)  - the tracer field in spectral space
    lamda (float)       - the lamda value in [1/seconds] determining the strength of relaxation to environmen
    
    RETURN:
    chi (spharm object) - the approximated tendency delta_chi/delta_t tracer due to relaxation 
    
    '''
    
    relax = lamda * chi 
  
    return relax

def interpolate_variable_to_ml(pres, temporal_change_t_clim_on_pres):
    ''' Helperfunction. Interpoltates the variable temporal_change_t_clim_on_pres given on pressure levels to model levels.
    
    INPUT:
    pres (numpy array)                              - pressure field on model levels
    temporal_change_t_clim_on_pres (numpy array)    - temporal change of climatological (potential) temeprature on pressure levels

    RETURN:
    temporal_change_t_clim_on_ml (numpy array)  - temporal change of climatological (potential) temeprature on model levels
    
    '''
    
    # make an xarray of temporal_change_t_clim_on_pres_xarray for easier handling
    temporal_change_t_clim_on_pres_xarray = xr.DataArray(temporal_change_t_clim_on_pres, coords={'level':target_levels_pressure, 'latitude':lat, 'longitude':lon}, dims=['level', 'latitude', 'longitude'])

    # sort by longitude axis such that it goes from -180 to 180
    # sort by latitude axis such that it goes from -90 to 90
    temporal_change_t_clim_on_pres_xarray = temporal_change_t_clim_on_pres_xarray.sortby('longitude').sortby('latitude')

    # fill nans with last valid value above surface
    mask = xr.where(np.isnan(temporal_change_t_clim_on_pres_xarray),1,0)
    indices = mask.diff('level').argmax('level')
    temporal_change_t_clim_on_pres_xarray = xr.where(np.isnan(temporal_change_t_clim_on_pres_xarray),temporal_change_t_clim_on_pres_xarray[indices],temporal_change_t_clim_on_pres_xarray)

    # where pressure is out of range, set pressure to last valid value from temperature climatology
    original_shape = np.shape(pres)
    pres_masked = np.where(pres>target_levels_pressure[-1].values,target_levels_pressure[-1].values,pres)
    pres_masked = np.where(pres<target_levels_pressure[0].values,target_levels_pressure[0].values,pres_masked)

    # get sample data
    sample = np.stack((pres_masked, Lat, Lon), axis=-1)

    # make grid
    x = temporal_change_t_clim_on_pres_xarray.level.values
    y = temporal_change_t_clim_on_pres_xarray.latitude.values
    z = temporal_change_t_clim_on_pres_xarray.longitude.values

    # interpolate to modellevels
    temporal_change_t_clim_on_ml = interpn((x, y, z), temporal_change_t_clim_on_pres_xarray.values, sample).reshape(original_shape)
        
    return temporal_change_t_clim_on_ml

def get_climatological_temperature_gradients_on_ml(pres, t_clim_on_pres, tracermode):
    ''' Helperfunction. Computes the horizontal/vertical climatological (potential) temperature gradient on pressure levels based on the (potential) temperature climatology on pressure levels.
    Then, interpolates the computed climatological (potential) temeprature gradient to model levels. The others are assigned empty lists.
    
    INPUT:
    pres (numpy array)              - pressure field on model levels
    t_clim_on_pres (numpy array)    - climatological mean (potential) temperature climatology on pressure levels
    tracermode (str)                - the tracermode defining which gradient should be computed;  either horizontal_temp, horizontal_theta, vertical_temp, vertical_theta
    
    RETURN:
    either grad_t_clim_on_ml_u and grad_t_clim_on_ml_v (numpy arrays)   - the zonal/meridional climatological (potential) temperature gradient model levels
    or grad_t_clim_on_ml_w (numpy array)                                - the vertical climatological (potential) temperature gradient on model levels
 
    '''
    
    # horizontal gradient
    if tracermode == 'horizontal_temp' or tracermode == 'horizontal_theta':

        # make an xarray of t_clim_on_pres_xarray for easier handling
        t_clim_on_pres_xarray = xr.DataArray(t_clim_on_pres, coords={'level':target_levels_pressure, 'latitude':lat, 'longitude':lon}, dims=['level', 'latitude', 'longitude'])
        
        # sort by longitude axis such that it goes from -180 to 180
        # sort by latitude axis such that it goes from -90 to 90
        t_clim_on_pres_xarray = t_clim_on_pres_xarray.sortby('longitude').sortby('latitude')

        # compute zonal temperature gradient with centered differences  
        # multiply by conversion_factor_lon to convert unit of gradient from K/° to K/m
        conversion_factor_lon = 360 / (2 * np.pi * RSPHERE * np.cos(np.deg2rad(t_clim_on_pres_xarray.latitude)))
        grad_t_clim_on_pres_u = (t_clim_on_pres_xarray.differentiate('longitude')) * conversion_factor_lon

        # fill nans with last valid value above surface
        # first, find indices of last valied value
        # then use this to fill nans
        # procedure is identical to that in xarray's ffill()-method, but for this the module bottleneck is needed, which was not available
        mask = xr.where(np.isnan(grad_t_clim_on_pres_u),1,0)
        indices = mask.diff('level').argmax('level')
        grad_t_clim_on_pres_u = xr.where(np.isnan(grad_t_clim_on_pres_u),grad_t_clim_on_pres_u[indices],grad_t_clim_on_pres_u)
        
        # compute meridional temperature gradient with centered differences  
        # multiply by conversion_factor_lat to convert unit of gradient from K/° to K/m
        conversion_factor_lat = 360 / (2 * np.pi * RSPHERE)
        grad_t_clim_on_pres_v = t_clim_on_pres_xarray.differentiate('latitude') * conversion_factor_lat

        # fill nans with last valid value above surface
        mask = xr.where(np.isnan(grad_t_clim_on_pres_v),1,0)
        indices = mask.diff('level').argmax('level')
        grad_t_clim_on_pres_v = xr.where(np.isnan(grad_t_clim_on_pres_v),grad_t_clim_on_pres_v[indices],grad_t_clim_on_pres_v)

        # set the zonal gradient at -90° and 90° to zero
        grad_t_clim_on_pres_u[:,0,:] = 0
        grad_t_clim_on_pres_u[:,-1,:] = 0

        # where pressure is out of range, set pressure to last valid value from temperature climatology
        original_shape = np.shape(pres)
        pres_masked = np.where(pres>target_levels_pressure[-1].values,target_levels_pressure[-1].values,pres)
        pres_masked = np.where(pres<target_levels_pressure[0].values,target_levels_pressure[0].values,pres_masked)
    
        # get sample data
        sample = np.stack((pres_masked, Lat, Lon), axis=-1)
         
        # make grid
        x = grad_t_clim_on_pres_u.level.values
        y = grad_t_clim_on_pres_u.latitude.values
        z = grad_t_clim_on_pres_u.longitude.values

        # get the temperature gradients in u and v directions at modellevels
        grad_t_clim_on_ml_u = interpn((x, y, z), grad_t_clim_on_pres_u.values, sample).reshape(original_shape) 
        grad_t_clim_on_ml_v = interpn((x, y, z), grad_t_clim_on_pres_v.values, sample).reshape(original_shape) 

        return grad_t_clim_on_ml_u, grad_t_clim_on_ml_v
    
    # vertical gradient
    elif tracermode == 'vertical_temp' or tracermode == 'vertical_theta':

        # where pressure is out of range, set pressure to last valid value from temperature climatology
        original_shape = np.shape(pres)
        pres_masked = np.where(pres>target_levels_pressure[-1].values,target_levels_pressure[-1].values,pres)
        pres_masked = np.where(pres<target_levels_pressure[0].values,target_levels_pressure[0].values,pres_masked)

        # get sample data
        sample = np.stack((pres_masked, Lat, Lon), axis=-1)

        # make xarray of t_clim_on_pres to change axis more easily and to caluclate vertical gradient more easily
        t_clim_on_pres_xarray = xr.DataArray(t_clim_on_pres, coords={'level':target_levels_pressure, 'latitude':lat, 'longitude':lon}, dims=['level', 'latitude', 'longitude'])
        
        # sort by longitude axis such that it goes from -180 to 180
        # sort by latitude axis such that it goes from -90 to 90
        t_clim_on_pres_xarray = t_clim_on_pres_xarray.sortby('longitude').sortby('latitude')

        # compute vertical gradient
        t_grad_on_pl = t_clim_on_pres_xarray.differentiate('level')

        # fill nans with last valid value above surface
        # first, find indices of last valied value
        # then use this to fill nans
        # procedure is identical to that in xarray's ffill()-method, but for this the module bottleneck is needed, which was not available
        mask = xr.where(np.isnan(t_grad_on_pl),1,0)
        indices = mask.diff('level').argmax('level')
        t_grad_on_pl = xr.where(np.isnan(t_grad_on_pl),t_grad_on_pl[indices],t_grad_on_pl)

        # make grid
        x = t_grad_on_pl.level.values
        y = t_grad_on_pl.latitude.values
        z = t_grad_on_pl.longitude.values

        # get clim. gradient at each grid point on modellevel
        grad_t_clim_on_ml_w = interpn((x, y, z), t_grad_on_pl.values, sample).reshape(original_shape)

        return grad_t_clim_on_ml_w

def source(*, u, v, w, omega, grad_t_clim_on_ml_u, grad_t_clim_on_ml_v, grad_t_clim_on_ml_w, temporal_change_t_clim_on_ml, pres, temp, diab_heat, tracermode):

    '''The approximated tendency delta_chi/delta_t due to the source term.
    The variables omega, pres, temp, diab_heat, grad_t_clim_on_ml_u, grad_t_clim_on_ml_v, grad_t_clim_on_ml_w, temporal_change_t_clim_on_ml are given to compute the respective source term.
    Depending on the tracer mode, data (numpy arrays) is only assigned to certain of these variables. The others are assigned empty lists.
    
    INPUT:
    u, v, w (numpy array)                                   - the zonal, meridional, and vertical wind 
    omega (numpy array/empty list)                          - vertical wind in pressure coordinates provided as a numpy array; if not needed empty list
    pres (numpy array/empty list)                           - pressure provided as a numpy array; if not needed empty list                            -
    temp (numpy array/empty list)                           - temperature provided as a numpy array; if not needed empty list
    diab_heat (numpy array/empty list)                      - diabatic heating rate provided as a numpy array; if not needed empty list
    grad_t_clim_on_ml_u (numpy array/empty list)            - climatological zonal temperature gradient on modellevels provided as a numpy array; if not needed empty list
    grad_t_clim_on_ml_v (numpy array/empty list)            - climatological meridional temperature gradient on modellevels provided as a numpy array; if not needed empty list
    grad_t_clim_on_ml_w (numpy array/empty list)            - climatological vertical temperature gradient on modellevels provided as a numpy array; if not needed empty list
    temporal_change_t_clim_on_ml (numpy array/empty list)   - temporal change of climatological temperature on modellevels provided as a numpy array; if not needed empty list
    tracermode (str)                                        - the name of the tracer
    
    RETURN:
    source (spharm object)  - the approximated tendency delta_chi/delta_t tracer due to the source term
    

    '''

    if tracermode == 'pressure':
    
        # take omega as source, convert omega from Pa/s in hPa/s
        source = -(omega/100)

    elif tracermode == 'latitude':

        # convert velocity from m/s to °/s
        conversion_factor = 360 / (2 * np.pi * RSPHERE)
        source = - conversion_factor * v
    
    elif tracermode == 'horizontal_temp' or tracermode == 'horizontal_theta':

        # compute u*grad t_clim
        source = u * grad_t_clim_on_ml_u + v * grad_t_clim_on_ml_v 

    elif tracermode == 'vertical_temp' or tracermode == 'vertical_theta':
         
        # convert omega from Pa/s in hPa/s
        omega = omega / 100

        # compute omega * (grad t_clim)
        source =  omega * grad_t_clim_on_ml_w 
                
        if tracermode == 'vertical_temp':

            # subtract adiabatic warming
            source =  source - omega * (0.285 * temp / pres )

    elif tracermode == 'diabatic_theta' or tracermode == 'diabatic_temp':
        
        source = -diab_heat
    
        if tracermode == 'diabatic_theta':
            source = source / ((pres/1013.25)**0.285)

    elif tracermode == 'seasonality_theta' or tracermode == 'seasonality_temp':
        source = temporal_change_t_clim_on_ml

    # move vertical axis to the back
    source = np.moveaxis(source, 0, -1)

    # transform to spectral space
    source = s.grdtospec(source)

    return source

def get_vertical_gradient(*, chi, w):
    '''Get the vertical gradient of the tracer field. Second order central differences are used.
    
    INPUT:
    chi (spham object)  - the tracer field in spectral space
    w (inumpy array)    - the vertical wind (eta vertical velocity) in physical space
    
    RETURN:
    grad_w (numpy array) - the vertical gradient in physical space
    
    '''
    
    # transform the tracer field to physical space
    chi_space = s.spectogrd(chi)
    
    # second order central differences are calculated
    # at the upper and lower boundary, one sided gradients are used
    delta_chi = np.gradient(chi_space,axis=2)
    grad_w = delta_chi / Delta_eta

    return grad_w
    
def advection(*, chi, u, v, w):
    '''The approximated tendency delta_chi/delta_t due to horizontal and vertical advection. Calculated from approximated horizontal and vertical gradients of tracer field.
    
    INPUT:
    chi (spham object)      - the tracer field in spectral space
    u, v, w (numpy array)   - the zonal, meridional, and vertical wind (eta vertical velocity) in physical space

    RETURN:
    advection_space (spharm object)     - the approximated tendency delta_chi/delta_t due to advection
    
    '''

    # get the horizontal and vertical gradients of the tracer field
    grad_u, grad_v = get_horizontal_gradients(chi)
    grad_w = get_vertical_gradient(chi=chi, w=w)

    # total tendency due to advection
    advection_space = np.moveaxis(u, 0, -1) * grad_u + np.moveaxis(v, 0, -1) * grad_v + np.moveaxis(w, 0, -1) * grad_w  
        
    # transform to spectral space
    advection_space = s.grdtospec(advection_space)
    
    return advection_space

