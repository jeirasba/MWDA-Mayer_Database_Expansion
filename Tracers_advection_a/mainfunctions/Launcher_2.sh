
# vertical
/home/jorge/miniconda3/envs/mwda307/bin/python main_ERA5_lamda.py --starting_date 2020-08-29 --starting_hour 0 --ending_date 2020-08-29 --ending_hour 18 --tracer vertical_theta --lamda_reciprocal_days 3 --savedir ./test_vertical_theta/
# seasonality
/home/jorge/miniconda3/envs/mwda307/bin/python main_ERA5_lamda.py --starting_date 2020-08-29 --starting_hour 0 --ending_date 2020-08-29 --ending_hour 18 --tracer seasonality_theta --lamda_reciprocal_days 3 --savedir ./test_seasonality_theta/
# diabatic (variante theta)
/home/jorge/miniconda3/envs/mwda307/bin/python main_ERA5_lamda.py --starting_date 2020-08-29 --starting_hour 0 --ending_date 2020-08-29 --ending_hour 18 --tracer diabatic_theta --lamda_reciprocal_days 3 --savedir ./test_diabatic_theta/
