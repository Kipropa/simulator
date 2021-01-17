
import sys
if '..' not in sys.path:
    sys.path.append('..')

import random as rd
import pandas as pd
from lib.measures import *
from lib.experiment import Experiment, options_to_str, process_command_line
from lib.calibrationSettings import calibration_lockdown_dates, calibration_start_dates, calibration_lockdown_beta_multipliers
from lib.calibrationFunctions import get_calibrated_params, get_unique_calibration_params

TO_HOURS = 24.0

if __name__ == '__main__':

    name = 'calibration-steps'
    random_repeats = 48
    full_scale = True
    verbose = True
    seed_summary_path = None
    set_initial_seeds_to = None

    # command line parsing
    args = process_command_line()
    country = args.country
    area = args.area
    cpu_count = args.cpu_count
    maxBOiters = 40 if area in ['BE', 'JU', 'RH'] else None

    # seed
    c = 0
    np.random.seed(c)
    rd.seed(c)

    # set simulation and intervention dates
    start_date = calibration_start_dates[country][area]
    end_date = calibration_lockdown_dates[country]['end']
    measure_start_date = calibration_lockdown_dates[country]['start']
    measure_window_in_hours = dict()
    measure_window_in_hours['start'] = (pd.to_datetime(measure_start_date) - pd.to_datetime(start_date)).days * TO_HOURS
    measure_window_in_hours['end'] = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days * TO_HOURS

    # create experiment object
    experiment_info = f'{name}-{country}-{area}'
    experiment = Experiment(
        experiment_info=experiment_info,
        start_date=start_date,
        end_date=end_date,
        random_repeats=random_repeats,
        cpu_count=cpu_count,
        full_scale=full_scale,
        verbose=verbose,
    )

    # Load calibrated parameters up to `maxBOiters` iterations of BO
    unique_calibration_params = get_unique_calibration_params(
        country=country, area=area,
        multi_beta_calibration=False,
        maxiters=maxBOiters)

    unique_calibration_params = [unique_calibration_params[-1]]

    for iteration, calibrated_params in unique_calibration_params:
        print(iteration - 20, calibrated_params)

    # run model fit plot for each improved setting
    for iteration, calibrated_params in unique_calibration_params:

        # experiment parameters
        p_stay_home = calibrated_params['p_stay_home']

        # measures
        max_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days

        m = [
            SocialDistancingForAllMeasure(
                t_window=Interval(
                    measure_window_in_hours['start'], 
                    measure_window_in_hours['end']),
                p_stay_home=p_stay_home),

            BetaMultiplierMeasureByType(
                t_window=Interval(
                    measure_window_in_hours['start'], 
                    measure_window_in_hours['end']),
                beta_multiplier=calibration_lockdown_beta_multipliers)
            ]

        simulation_info = options_to_str(iter=iteration)

        experiment.add(
            simulation_info=simulation_info,
            country=country,
            area=area,
            measure_list=m,
            lockdown_measures_active=False,
            test_update=None,
            seed_summary_path=seed_summary_path,
            set_calibrated_params_to=calibrated_params,
            set_initial_seeds_to=set_initial_seeds_to,
            full_scale=full_scale)

    print(f'{experiment_info} configuration done.')
    
    # execute all simulations
    experiment.run_all()

