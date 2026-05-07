# Python code implementing the tracer method by Mayer and Wirth (2023)

This git repository contains python code implementing the tracer method outlined in Mayer and Wirth (2023): "Lagrangian description of the atmospheric flow from Eulerian tracer advection with relaxation" and applied in Mayer and Wirth (2024): "Lagrangian characterization of heat waves: The perspecive matters".
The method and characteristics of the algorithm are explained in Sections 2 and 3 of Mayer and Wirth (2023). Further information about the method is also provided in Section 2 of Mayer and Wirth (2024). 
The algorithm solves the advection-relaxation problem for 3D atmospheric flow on a global domain. The algorithm uses a pseudo-spectral approach.

The code in this branch solves the advection-relaxation problem in the form of equation (18) of Mayer and Wirth (2023). This may differ from other branches where equations (19)/(29) are solved.

## Data and algorithm

### Input data

The current version of the code uses global ERA5 reanalysis data on hybrid sigma/pressure model levels (Hersbach et al., 2017i, provided by the Copernicus Climate Change Service) on a regular latitude-longitude grid. Commonly, a horizontal resolution of 1° x 1° is used. 
Required variables for driving the advection algorithm are 
* u: the zonal wind [m/s], 
* v: the meridional wind [m/s], 
* etadot: the eta-coordinate vertical velocity [1/s]. 
Further, the variable
* sp: surface pressure [Pa] 
is needed to interpolate the final output from model levels to pressure levels. 

Depending on the tracer, further variables are required:
The tracers diabatic_theta and diabatic temp require parcel-based diabatic heating rates given by
* mttpm: the mean temperature tendency due to parametrisations [K/s] 
The tracers horizontal_theta, vertical_theta, and seasonality_theta require a climatological mean potential temperature 
* t: the climatological mean potential temperature value [K]
Likewise, the tracers horizontal_temp, vertical_temp, ans seasonality_temp require a climatoligical mean temperature
* t: the climatological mean temperature value [K] 
Vertical_theta and vertical_temp further require
* w: the pressure vertical velocity [Pa/s] (commonly known as omega)

The input data must be available as netcdf files, whereby each netcdf file may only contain one time step. The filenames must include the year, month, day, and hour for which the data are valid. The variables can either be provided in one file or in several files. 

The variables must have the dimensions
* time: time
* lat: latitude [degrees north] (can also be named "latitude")
* lon: longitude [degrees east] (can also be named "longitude")
* level: model level number 

A climatological mean (potential) temperature is not provided directly in the ERA5 data set, but must be calculated by the user. The current version of the code uses a climatology calculated on pressure levels. Thus, the dimensions for this data must be
* time: time
* lat: latitude [degrees north]
* lon: longitude [degrees east]
* level: pressure [hPa]  

Some example files are provided in the folder "exampledata". If the input files differ in any way from the example data, the code may need to be adapted accordingly. 

### Output data
Fields of the advected tracer field on a global regular latitude-longitude grid linearly interpolated from model levels to pressure levels. The fields are stored in netcdf files named chi_on_pl_YYYY-MM-DD_HH_IIIII.nc, where YYYY corresponds to the valid year, MM to the valid month, DD to the valid day, HH to the valid hour, and IIIII to the valid timestep. 
The netcdf files contain the variable
* chi_pl: advected tracer field [unit specific to the tracer]
with dimensions
* time: time
* level: pressure [hPa] 
* latitude: latitude [degrees north]
* longitude: longitude [degrees east]

### Implemented tracers
* pressure
* latitude
* horizontal_temp and horizontal_theta (for computing the contribution to a (potential) temperature anomaly from horizontal transport accross climatological (potential) temperature gradients)
* vertical_temp and vertical_theta (for computing the contribution to a (potential) temperature anomaly from vertical transport accross climatological (potential) temperature gradients)
* diabatic_temp and diabatic_temp (for computing the contribution to a (potential) temperature anomaly from diabatic heating; caution: the results from these tracers do not seem to be fully reliable) 
* seasonality_temp and seasonality_theta (for computing the contribution to a (potential) temperature anomaly from local changes in the (potential) temperature climatology over time)

### Algorithm
A pseudo-spectral method is applied. Input and output data are on a regular latitude-longitude grid while horizontal spatial derivatives are evaluated in spectral space with the help of spherical harmonics. The integration is done in spectral space. As time scheme the third order Runge Kutta scheme of Williamson is used.

## Structure of code

### ./mainfunctions
Methods to start the advection algorithm. 
* "main_ERA5_lamda.py": For starting the advection algorithm.
* "myconfigs.py": For specifying the input data etc. (This file must be adapted before running the algorithm!)
* ./files_for_jobsubmission_on_mogon: Files and sbatch scripts used to run the code on the high-performance computing cluster MOGON in Mainz. (May not relevant for the user.)
 
### ./implementation
The core of the code. It contains the methods to solve the advection-relaxation problem.
* "config.py" and "getData.py": Configuration of the set up (grid, input files, etc.) for the advection algorithm. Gets the input from "myconfigs.py"
* "initialChi.py": Functions for initialization of the tracer field.
* "model.py": The central part of the code. The integration method/algorithm to solve the advection-relaxation equation on the 3D globe.
* "output.py": Stores the output fields in .nc-files.
* "windsERA5.py": Methods for reading in the input data (winds, surface pressure, ...) for driving the tracer advection algorithm.
* "coefficients_ERA5.nc": File containing the model level coefficients. 

### ./exampledata 
Example input data (~2 2GB) for running a short example of the tracers latitude, horizontal_theta, or horizontal_temp.

## Python modules needed
* os
* sys
* numpy 
* xarray 
* spharm
* datetime
* time 
* stratify
* multiprocessing
* pathlib 
* argparse
* scipy.interpolate

The code has been used with Python 3.7.4.

## Manual
To run the code with the example data, proceed as follows:
* Adapt the "./mainfunctions/myconfigs.py" script by setting the variable "specification" to "example", i.e. "specification = example".
* Start the code from the bash console:
```
python main_ERA5_lamda.py --starting_date 2020-08-29 --starting_hour 3 --ending_date 2020-09-01 --ending_hour 18 --tracer TRACER --lamda_reciprocal_days 2 --savedir /DIR/TO/STORE/THE/OUTPUT
```
For TRACER you can choose latitude, horizontal_theta, horizontal_temp, seasonality_theta, or seasonality temp. Replace /DIR/TO/STORE/THE/OUTPUT by the directory name the output shall be stored to.  

To run the code with ERA5 reanalysis data other than the example data, proceed as follows:
* Get the required ERA5 data.
* Get/compute a (potential) temperature climatology on pressure levels.
* Adapt the "./mainfunctions/myconfigs.py" script by implementing a new specification. Here you specify important information about the input data, e.g. the path where you downloaded the data to. Use the existing specifications as a guide. Finally, set the variable "specification" to the name of your newly implemented specification. 
* Start the code from the bash console
```
python main_ERA5_lamda.py --starting_date YYYY-MM-DD --starting_hour H --ending_date YYYY-MM-DD --ending_hour H --tracer TRACER --lamda_reciprocal_days LAMBDA --savedir /DIR/TO/STORE/THE/OUTPUT
```
Choose YYYY-MM-DD, H, TRACER, LAMBDA, SAVEDIR accordingly. Type 
```
python main_ERA5_lamda.py -h
```
for help.

## References

Mayer, A. and Wirth, V.: Lagrangian characterization of heat waves: The perspective matters, Weather and Climate Dynamics, 2024. (preprint)

Mayer, A. and Wirth, V.: Lagrangian description of the atmospheric flow from Eulerian tracer advection with relaxation, Quarterly Journal
of the Royal Meteorological Society, 149, 1271–1292, https://doi.org/10.1002/qj.4453, 2023.

Hersbach, H., Bell, B., Berrisford, P., Hirahara, S., Horányi, A., Muñoz-Sabater, J., Nicolas, J., Peubey, C., Radu, R., Schepers, D., Simmons,
A., Soci, C., Abdalla, S., Abellan, X., Balsamo, G., Bechtold, P., Biavati, G., Bidlot, J., Bonavita, M., De Chiara, G., Dahlgren, P., Dee,
D., Diamantakis, M., Dragani, R., Flemming, J., Forbes, R., Fuentes, M., Geer, A., Haimberger, L., Healy, S., Hogan, R. J., Hólm, E.,
Janisková, M., Keeley, S., Laloyaux, P., Lopez, P., Lupu, C., Radnoti, G., de Rosnay, P., Rozum, I., Vamborg, F., Villaume, S., and Thépaut,
J.: Complete ERA5: Fifth generation of ECMWF atmospheric reanalyses of the global climate., Copernicus Climate Change Service (C3S)
Data Store (CDS), https://doi.org/10.24381/cds.143582cf, 2017.

## Contact
If you have any questions or suggestions, please do not hesitate to contact Amelie Mayer (amelie.mayer@uni-mainz.de). 

Feel free to play around. Have fun!

