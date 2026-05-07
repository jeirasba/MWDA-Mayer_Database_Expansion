#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  6 14:34:26 2020

@author: Amelie Mayer

Main script for starting the tracer algorithm.

"""

import os 
import sys

# append paths where python searches for modules
path_to_append = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'implementation'))
sys.path.append(path_to_append)
path_to_append = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.append(path_to_append)

import numpy as np
import time as tm
import datetime
import xarray as xr
import os
from pathlib import Path

from implementation import initialChi as ic
from implementation import windsERA5 
from implementation import model
from myconfigs import timesteps_used_per_hour as timesteps_per_hour
import argparse
            
def main(date_start, 
         initial_chi,
         hour_start=0, 
         args_initial_chi=[],  
         output_frequency=6, savedir='',  
         timesteps_per_hour=6, timesteps=24*6, 
         lamda=0,
         tracermode=None): 
    '''
    Main function which calls the integration function.
    
    INPUT:
    date_start (str)            - the starting date (Str), e.g. 2016-09-01
    initial_chi (a function)    - the initialization function returning for the tracer chi 
    hour_start (int)            - the starting hour, e.g. 6
    args_initial_chi            - arguments to give to the initialization function
    output_frequency (int)      - the output frequency in terms of timesteps
    savedir (str)               - the directory to store the output to
    timesteps_per_hour (int)    - the number of timesteps per hour used for integration, defined in implementation.config
    timesteps (int)             - the number of total timesteps to be perfomrmed
    lamda (int)                 - the lamda value in [1/s] determining the strength of relaxation
    tracermode (str)            - the tracer, either: 'pressure', 'latitude', 'horizontal_temp', 'horizontal_theta', 'vertical_temp', 'vertical_theta', 'diabatic_temp', 'diabatic_theta', 'seasonality_temp', 'seasonality_theta'
    
    '''
        
    # create the directory "savedir" to store the output
    Path(savedir).mkdir(parents=True, exist_ok=True)   
    
    # initialize the tracer chi
    chi_start = initial_chi(*args_initial_chi)
    
    # change longitudes from 0..360 to -180..180
    # if logitudes are already from -180..180, nothing will change
    chi_start = chi_start.assign_coords(longitude=(((chi_start.longitude + 180) % 360) - 180))

    # start clocking
    ta = tm.time()
    delta_t = (60 / timesteps_per_hour) * 60      # in seconds
    
    # print some infos
    print('TIMESTEPS: ' + str(timesteps),flush=True)
    
    # select which data/variables shall be read in
    if tracermode == 'diabatic_temp':
        variables = ['wind', 'p', 'diab_heating']

    elif tracermode == 'diabatic_theta':
        variables = ['wind', 'p', 'diab_heating']

    elif tracermode == 'horizontal_temp':
        variables = ['wind', 'p']

    elif tracermode == 'horizontal_theta':
        variables = ['wind', 'p']
    
    elif tracermode == 'vertical_temp':
        variables = ['wind', 'p', 't', 'omega']
    
    elif tracermode == 'vertical_theta':
        variables = ['wind', 'p', 'omega']
    
    elif tracermode == 'seasonality_theta':
        variables = ['wind', 'p']

    elif tracermode == 'seasonality_temp':
        variables = ['wind', 'p']

    elif tracermode == 'pressure':
        variables = ['wind', 'p', 'omega']
    
    elif tracermode == 'latitude':
        variables = ['wind', 'p']

    # start the integration
    model.integration(chi_start=chi_start,
                      wind=windsERA5.get_wind_data_ERA5,
                      args_wind=[date_start,timesteps_per_hour],
                      kwargs_wind={'hour_start':hour_start, 'variables':variables},
                      delta_t=delta_t, lamda=lamda, tracermode=tracermode,
                      timesteps=timesteps,
                      output_frequency=output_frequency,
                      savepath=savedir)   
    
    # end clocking
    tb = tm.time()
    
    # print total time
    total_time = tb - ta
    print("--- %s total seconds ---" % (total_time),flush=True)    
    
    # write the value of lamda and the total time to the "info.txt" file
    if savedir != '':
        file = open(os.path.join(savedir,'info.txt'), 'w')
        file.write('lamda = ' + str(lamda) + '\n' + 'total time (s) = ' + str(total_time))       

def initialization_function(tracer):
    '''Returns the initialization function for each individual tracer. In the current version of the code, this is the same for each of the tracers.'''

    return ic.initialize_with_zeros

def args_initialization_function(tracer, start_date, hour_start):
    '''Returns the arguments to give to the initialization function. In the current version of the code, no arguments are given to the initialization function.'''

    return []
    
def start_advection_of_tracer(start_date, start_hour, ref_date, ref_hour, tracer, lamda_reciprocal_days, savedir, output_frequency_hours=3):
        
    '''Start the advection algorithm.'''
   
    # print some information
    print('LAMBDA_RECIPROCAL_DAYS: ' + str(lamda_reciprocal_days) + ' days')
    print('TRACER: ' + tracer)
    print('START_DATETIME: ' + start_date + ' ' + start_hour + 'UTC')
    duration_hours = int((datetime.datetime.strptime(ref_date + ' ' + ref_hour,'%Y-%m-%d %H') - datetime.datetime.strptime(start_date + ' ' + start_hour,'%Y-%m-%d %H')).total_seconds() / (60 * 60))
    print('DURATION IN HOURS '+str(duration_hours))
    
    # calculate the lambda-value
    if lamda_reciprocal_days != 0:
        # calculate the lamda value in [1/s]
        lamda = 1 / (24 * 60 * 60 * args.lamda_reciprocal_days) 
    else:
        # to use no relaxation, set lambda = 0
        lamda = 0

    # start the tracer algorithm 
    main(start_date,
            initialization_function(tracer),
            hour_start=start_hour,
            args_initial_chi=args_initialization_function(tracer, start_date, start_hour),
            output_frequency=timesteps_per_hour * output_frequency_hours,
            timesteps_per_hour=timesteps_per_hour,
            timesteps=duration_hours * timesteps_per_hour,
            lamda=lamda,tracermode=tracer,
            savedir=os.path.join(savedir,'Advection_' + tracer + '_lamdarec' + str(lamda_reciprocal_days) + 'days_' + start_date + '_' + start_hour.zfill(2)),
            )
    
    print('Done.')
        
if __name__ == '__main__':
    
    # read in arguments given via the console, all arguments are required
    parser = argparse.ArgumentParser()
    parser._action_groups.pop() 
    required = parser.add_argument_group('required arguments')
    required.add_argument("--starting_date", help="the starting date of the run in the format YYYY-MM-DD, e.g. 2016-09-01", type=str, required=True)
    required.add_argument("--starting_hour", help="the starting hour of the run (no leading zero), e.g. 6", type=str, required=True)
    required.add_argument("--ending_date", help="the ending date of the run in the format YYYY-MM-DD, e.g. 2016-09-30", type=str, required=True)
    required.add_argument("--ending_hour", help="the ending date hour of the run (no leading zero), e.g. 6", type=str, required=True)
    required.add_argument("--tracer", help="the tracer", type=str, choices=["horizontal_theta","vertical_theta","horizontal_temp","vertical_temp","diabatic_temp","seasonality_theta","seasonality_temp","diabatic_theta","pressure","latitude"], required=True)
    required.add_argument("--lamda_reciprocal_days", help="the reciprocal of the lambda value in days, e.g. 5. Give '0' to use no relaxation.", type=float, required=True)
    required.add_argument("--savedir", help="the directory to store the output to ", type=str, required=True)
    args = parser.parse_args()
       
    # start the advection algorithm
    start_advection_of_tracer(args.starting_date, args.starting_hour, args.ending_date, args.ending_hour, args.tracer, args.lamda_reciprocal_days, args.savedir)
    
    # start the script from the "traceradvectionera5/mainfunctions" directory via the bash console, using e.g.
    # python main_ERA5_lamda.py --starting_date 2020-08-30 --starting_hour 3 --ending_date 2020-08-30 --ending_hour 15 --tracer latitude --lamda_reciprocal_days 3 --savedir /DIR/TO/SAVE/OUTPUT 
    # for help, do: python main_ERA5_lamda.py -h
 
        
