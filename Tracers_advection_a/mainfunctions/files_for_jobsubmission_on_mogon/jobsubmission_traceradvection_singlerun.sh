#!/bin/bash
#SBATCH -A m2_jgu-w2w	     
##SBATCH -p devel
#SBATCH -p smp
#SBATCH -C anyarch
#SBATCH -N 1                  
#SBATCH -n 1                 
#SBATCH -c 2		     
#SBATCH --mem=40G
#SBATCH -t 01:30:00          
#SBATCH -J traceradvection
#SBATCH -o single_run.log

# load the python module and start the virtual environment
module purge
module load lang/Python/3.7.4-GCCcore-8.3.0 
which python
source ~/CODE/start_traceradvectionera5/my_venv_traceradvection/bin/activate 
which python

# start the tracer advection algorithm
srun --unbuffered python ../main_ERA5_lamda.py --starting_date 2020-02-20 --starting_hour 0 --ending_date 2020-03-02 --ending_hour 0 --tracer horizontal_theta --lamda_reciprocal_days 7 --savedir /lustre/miifs01/project/m2_jgu-w2w/w2w/amayer02/TRACEROUTPUT/final_check_clim_advection_directly



