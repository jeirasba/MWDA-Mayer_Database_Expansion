#!/bin/bash
#SBATCH -A m2_jgu-w2w	     
#SBATCH -p smp
#SBATCH -C anyarch
#SBATCH -N 1                  
#SBATCH -n 1                 
#SBATCH -c 2		     
#SBATCH --mem=40G
#SBATCH -t 03:00:00
#SBATCH -J traceradvection              
#SBATCH -o traceradvection_%A_%a.log    # name of the outputfile, %A stands for the jobID, %a stands for the ID of the specific job within the job array
#SBATCH --array=1-30    

START_DATE=$(sed -n "${SLURM_ARRAY_TASK_ID}"p files_runs_with_lambda0/start_dates.txt)
END_DATE=$(sed -n "${SLURM_ARRAY_TASK_ID}"p files_runs_with_lambda0/end_dates.txt)
TRACER=$(sed -n "${SLURM_ARRAY_TASK_ID}"p files_runs_with_lambda0/list_tracers.txt)			     # read in tracer corresponding to year
SAVEDIR=/lustre/miifs01/project/m2_jgu-w2w/w2w/amayer02/TRACEROUTPUT/2010-2022_lambda0_tracerdiagnostics/acc_period7 # the directory to save the output to
mkdir -p $SAVEDIR/$YEAR

# load python module and start virtual environment
module purge
module load lang/Python/3.7.4-GCCcore-8.3.0 
which python
source ~/CODE/start_traceradvectionera5/my_venv_traceradvection/bin/activate # its corresponding python module needs to be loaded first

# print some infos
echo $START_DATE
echo $END_DATE
echo $TRACER
echo $SAVEDIR

# start the tracer algorithm; for each year an individual run is started 
srun --unbuffered python ../main_ERA5_lamda.py --starting_date $START_DATE --starting_hour 18 --ending_date $END_DATE --ending_hour 18 --tracer ${TRACER}_temp --lamda_reciprocal_days 0 --savedir ${SAVEDIR}/${YEAR} 


