import argparse
import numpy as np
import yaml
import pandas as pd
import dolfin as df
import os

from simulation.elasticity_estimation import estimate_elasticity_displacementloss
from simulation.helpers import set_ffc_params, pretty_print_dict, simpleheartlogger

#OPTIMIZATION PARAMETERS
OPT_ALGORITHM = "TNC" #trust-krylov
OPT_TOL = 1e-6
DISP_NOISE = 0.5

def convert_numpy_scalars_to_python(data):
    """Recursively convert numpy scalar values to Python native types."""
    if isinstance(data, dict):
        return {key: convert_numpy_scalars_to_python(value) for key, value in data.items()}
    elif isinstance(data, np.generic):  # Check for numpy scalar types
        return float(data)
    elif isinstance(data, list):
        return [convert_numpy_scalars_to_python(item) for item in data]
    else:
        return data

def main(energy_function, scenario):
    set_ffc_params()
    df.set_log_level(40)
    
    experiment_params = yaml.load(open("experiment_params.yaml", "r"), Loader = yaml.SafeLoader)

    simulation_params = yaml.load(open("simulation/simulation_config.yaml", "r"), Loader = yaml.SafeLoader)
    lhs_sample = pd.DataFrame(experiment_params["latin_hypercube_samples"][scenario][energy_function])
    
    run_nums = np.arange(args.run_start, args.run_end)
    lhs_subsample = lhs_sample.iloc[run_nums]

    #Pick scenario appropriate boundary conditions and compressibility
    simulation_params["numerics"]["base_spring_k"] =  simulation_params["numerics"]["base_spring_k"][scenario]
    simulation_params["numerics"]["compress"] =  simulation_params["numerics"]["compress"][scenario]
    simulation_params["energy_function"] = energy_function
    
    simulation_params["mesh"]["path"] =  f"3Dsimulation_data/{energy_function}/{scenario}/unloaded_geo.hdf5"
    simulation_params["mesh"]["microstructure"] =  f"3Dsimulation_data/{energy_function}/{scenario}/unloaded_geo_microstructure.h5"
    simulation_params["mechdata"] = f"3Dsimulation_data/pressure_traces/{scenario}_traces.csv"
    simulation_params["elasticity_estimation"]["lower_bound"] = list(experiment_params["optimization_lower_bounds"][scenario][energy_function].values()) #Update in the data

    for i, lhs_params in lhs_subsample.iterrows():
        simulation_params["output"]["files"]["path"] = f"results/{energy_function}/{scenario}/{i}"
        simulation_params["output"]["files"]["logfile"] = f"results/{energy_function}/{scenario}/{i}/parameter_estimation.log"
        simulation_params["material_parameters"] = dict(lhs_params)

        simpleheartlogger.logpath = f"results/{energy_function}/{i}/paramest.log"
        
        simulation_params["elasticity_estimation"]["displacement_db"] = f"3Dsimulation_data/{energy_function}/{scenario}/noisy_disps/{i}_{DISP_NOISE}.hdf5"
        
        simpleheartlogger.log(pretty_print_dict(simulation_params))
        
        config_file = os.path.join(simulation_params["output"]["files"]["path"], "config_params.yaml")
        
        if not os.path.exists(os.path.dirname(config_file)):
            os.makedirs(os.path.dirname(config_file))

        yaml.dump(convert_numpy_scalars_to_python(simulation_params),
                  open(config_file, "w"), 
                  default_flow_style = False)
        estimate_elasticity_displacementloss(simulation_params)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-energy_function",
        choices = ["chesra1", "chesra2", "martonova3", "holzapfel-ogden"],
        default = "chesra1"
    )

    parser.add_argument("-scenario",
        choices = ["in_vivo_CMR", "ex_vivo_Klotz"],       
        default = "in_vivo_CMR"
    )

    parser.add_argument("-run_start",
                          type = int,
                          default = 0)

    parser.add_argument("-run_end",
                          type = int,
                          default = 20)
    args = parser.parse_args()
    main(args.energy_function, args.scenario)