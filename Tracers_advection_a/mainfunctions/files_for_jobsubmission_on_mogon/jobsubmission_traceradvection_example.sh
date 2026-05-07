#!/bin/bash

#SBATCH -A m2_jgu-w2w	     
#SBATCH -p smp
#SBATCH -C anyarch
#SBATCH -N 1                  
#SBATCH -n 1                 
#SBATCH -c 2		     
#SBATCH --mem=40G
#SBATCH -t 00:20:00
#SBATCH -J traceradvection
#SBATCH -o example.log

# load the python module and start the virtual environment
module purge
module load lang/Python/3.7.4-GCCcore-8.3.0
which python
source ~/CODE/start_traceradvectionera5/my_venv_traceradvection/bin/activate 
which python

# start the tracer algorithm
srun --unbuffered python ../main_ERA5_lamda.py --starting_date 2020-08-29 --starting_hour 3 --ending_date 2020-09-01 --ending_hour 15 --tracer latitude --lamda_reciprocal_days 2 --savedir /lustre/miifs01/project/m2_jgu-w2w/w2w/amayer02/TRACEROUTPUT/example_run



