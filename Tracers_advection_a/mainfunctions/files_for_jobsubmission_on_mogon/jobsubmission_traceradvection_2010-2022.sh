#!/bin/bash
#SBATCH -A m2_jgu-w2w	     
#SBATCH -p smp
#SBATCH -C anyarch
#SBATCH -N 1                  
#SBATCH -n 1                 
#SBATCH -c 2		     
#SBATCH --mem=40G
#SBATCH -t 40:00:00
#SBATCH -J traceradvection              
#SBATCH -o traceradvection_%A_%a.log    # name of the logfile, %A stands for the jobID, %a stands for the ID of the specific job within the job array
#SBATCH --array=1-13     		# the job array

YEAR=$(sed -n "${SLURM_ARRAY_TASK_ID}"p list_years_2010-2022.txt)     	# read in start years; job number 1 reads in first line of file, job number 2 reads in second line of file, ...
TRACER=$(sed -n "${SLURM_ARRAY_TASK_ID}"p list_tracers.txt)		# read in tracer corresponding to year
SAVEDIR=/lustre/miifs01/project/m2_jgu-w2w/w2w/amayer02/TRACEROUTPUT/2010-2022_tracerdiagnostics/lambda7/  # the directory to save the output to
mkdir -p $SAVEDIR/$YEAR

# load python module and start virtual environment
module purge
module load lang/Python/3.7.4-GCCcore-8.3.0 
which python
source ~/CODE/start_traceradvectionera5/my_venv_traceradvection/bin/activate # its corresponding python module needs to be loaded first

# print some infos
echo $YEAR
echo $TRACER
echo $SAVEDIR

# start the tracer algorithm; for each year an individual run is started 
srun --unbuffered python ../main_ERA5_lamda.py --starting_date $YEAR-02-20 --starting_hour 0 --ending_date ${YEAR}-09-30 --ending_hour 18 --tracer ${TRACER}_theta --lamda_reciprocal_days 7 --savedir ${SAVEDIR}/${YEAR} 


