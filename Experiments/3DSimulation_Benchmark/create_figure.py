from pathlib import Path
from matplotlib import pyplot as plt
import argparse
import os
import pandas as pd
import yaml
import ast
import re
import numpy as np
import seaborn as sns

import matplotlib.patches as mpatches
import matplotlib.lines as mlines

cmap = plt.get_cmap('viridis')
EFUNC_COLORS = {
    "chesra1": cmap(0.0),
    "chesra2": cmap(0.2),
    "martonova3": cmap(0.3),
    "MA":  cmap(0.4),
    "CL": cmap(0.6),
    "PZL": cmap(0.7),
    "holzapfel-ogden":  cmap(0.8)
}
PARAM_ORDERS = {"chesra1": ["p1", "p2", "p3"],
                "chesra2": ["p1", "p2", "p3", "p4"],                
                "martonova3": ["mu", "a_f", "b_f", "a_n", "b_n"],
                "holzapfel-ogden": ["a", "b", "a_f", "b_f", "a_s", "b_s", "a_fs", "b_fs"]}

EFUNC_SYMB = {
    "chesra1": "$\psi_{CH1}$",
    "chesra2": "$\psi_{CH2}$",
    "holzapfel-ogden": "$\psi_{HO}$",
    "martonova3": "$\psi_{MA}$"
}

PNAMES={"chesra1": {"p1": "p_{f-fs}", "p2": "p_{iso}", "p3": "p_{coup}"},
        "chesra2": {"p1": "p_{glob}", "p2": "p_{s-iso}", "p3": "p_{f-s}", "p4": "p_{f-iso}"},
}

RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

def gather_results():
    matparam_names_all = {}
    results_all = {}
    for dirpath, dirnames, filenames in os.walk(RESULTS_FOLDER):
        if "optresults.txt" in filenames:
            energy_function, scenario, run_number = Path(dirpath).parts[-3:]

            #config_params = yaml.load(open(config_params_path, "r"))
            optresults = open(os.path.join(dirpath, "optresults.txt"), "r").readlines()
            optresults = parse_optresult_file(optresults)
            matparam_estvals = optresults["x"]

            fun = optresults.get("fun")
            nfev = optresults.get("nfev")
            
            #Extract all numbers from the Run-time string
            runtime = re.findall(r"[-+]?\d*\.?\d+", optresults.get("Run-time"))
            assert(len(runtime)) == 1
            runtime = float(runtime[0])

            loss_lines, loss_vals= find_total_loss_values(os.path.join(dirpath, "paramest.log"))
            initial_fun = loss_vals[0]

            config_params_path = os.path.join(dirpath, "config_params.yaml")
            config_params = yaml.load(open(config_params_path, "r"), Loader = yaml.SafeLoader)
            
            matparam_names = config_params["material_parameters"].keys()
            matparam_inivals = list(config_params["material_parameters"].values())

            if not energy_function in results_all.keys():
                results_all[energy_function] = []
                matparam_names_all[energy_function] = matparam_names

            new_results = [scenario,
                           run_number,
                           initial_fun,
                           fun,
                           nfev,
                           runtime] + matparam_inivals + matparam_estvals
            
            results_all[energy_function].append(new_results)
    output_results(results_all, matparam_names_all)

def output_results(results_all, matparam_names_all):
    output_folder = os.path.join("results", "gathered")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for energy_function, results in results_all.items():
        ini_names = ["ini_" + name for name in matparam_names_all[energy_function]]
        est_names = ["est_" + name for name in matparam_names_all[energy_function]]
        other_names = ["scenario", "run number", "ini fun", "fun", "nfev", "runtime"]
        df = pd.DataFrame(results, columns = other_names + ini_names + est_names)
        output_file = os.path.join(output_folder, energy_function + "_results.csv")
        
        df = df.sort_values(by = ["run number"])
        df.to_csv(output_file, index=False)

        print("Results have been saved to", output_file)

def parse_array_string(array_string):
    # Remove the leading and trailing square brackets
    array_string = array_string.strip('[]')
    
    # Use regex to find all numbers, including those in scientific notation
    numbers = re.findall(r'[\d\.\+\-e]+', array_string)
    
    # Convert the found strings to floats
    numbers = [float(num) for num in numbers]
    
    return numbers

def parse_optresult_file(optresults):
    # Initialize an empty dictionary
    result_dict = {}
    # Iterate over each string in the list
    for i in range(len(optresults)):
        current_line = optresults[i]
        
        if ":" not in current_line:
            #print("skipped\n\t", current_line)
            continue

        # Split each string at the first occurrence of ':'
        key, value = current_line.split(':', 1)
        # Trim whitespace from key and value
        key = key.strip()
        value = value.strip()
        # Remove newline characters
        value = value.replace('\n', '')
        # Check if value starts with 'array' and evaluate it
        if value.startswith('array') or value.startswith('['):
             # Initialize a variable to hold the concatenated array definition
            if value.startswith('array'):
                 array_definition = value.split('array', 1)[1].strip()
            elif value.startswith('['):
                array_definition = value
            
            # Check if the array definition spans multiple lines
            j = i +1

            # Before the loop where you concatenate next_line to array_definition
            while array_definition.endswith('\\') or ('[' in array_definition and ']' not in array_definition) or ('(' in array_definition and ')' not in array_definition):
                # Read the next line. This part depends on how you're reading the file.
                next_line = optresults[j]  # Replace this with actual code to read the next line
                
                # Remove line continuation character if present and strip whitespace
                next_line = next_line.replace('\\', ' ').strip()
                
                # Concatenate the next line to the array definition
                array_definition += " " + next_line
                j += 1

            # Once the complete array definition is obtained, evaluate it
            value = parse_array_string(array_definition)
        else:
            try:
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
            except ValueError:
                pass  # Keep the value as is if it's not a number
        # Add the key-value pair to the dictionary
        result_dict[key] = value
    return result_dict

def find_total_loss_values(file_path):
    # Define the regex pattern to match "Total loss = xx.xx" and capture the float value
    pattern = r"Total loss = ([+-]?\d*\.\d+|\d+)"
    
    matching_lines = []
    loss_values = []
    
    # Open the file and read line by line
    with open(file_path, 'r') as file:
        for line in file:
            match = re.search(pattern, line)
            if match:
                matching_lines.append(line.strip())
                loss_values.append(float(match.group(1)))  # Extract and convert the loss value to float
    
    return matching_lines, loss_values

def get_xlabels(paramnames, efunc):
    x_labels = [
        "$\mathrm{\\mu}$" if pname == "mu"
        else "$\mathrm{" + "{}".format(PNAMES[efunc][pname]) + "}$" if pname.startswith("p") and pname[1:].isdigit()
        else "$\mathrm{" + pname.replace('_', '_{') + '}}$' if '_' in pname
        else "$\mathrm{" + pname + "}$"
        for pname in paramnames
    ]
    return x_labels

def plot_paramrange(efunc, paramnames, opt_params_lhs, gt_params, ax, color, title = None):
    x_labels = get_xlabels(paramnames, efunc)

    paramords = ["est_" + p for p in paramnames]
    est_params = opt_params_lhs[paramords]
    est_params.columns = paramnames

    #ax.grid(zorder = 0)
    long_df = pd.melt(est_params,
                      value_vars=paramnames,
                      var_name="Parameter",
                      value_name="Value")

    sns.boxplot(x="Parameter",
                y="Value",
                data=long_df,
                ax=ax,
                color = color,
                zorder = 10,
                order=paramnames,
        )
    
    ax.set_xlabel("")
    # Plot true values as red horizontal lines
    for i, pname in enumerate(paramnames):
        true_val = gt_params[pname]
        ax.hlines(
            y=true_val,
            xmin=i - 0.4,
            xmax=i + 0.4,
            colors="red",
            linestyles="--",
            linewidth=2,
            zorder=20,
            label = "Benchmark value",
        )

    if title:
        ax.set_title(title, loc = "left", fontsize = 16, weight = "bold")
    
    ax.set_xticklabels(x_labels)
    ax.set_ylabel("")
    ax.set_yscale("log")

def plot_results():
    gt_params = yaml.load(open("experiment_params.yaml", "r"), Loader = yaml.SafeLoader)["ground_truth"]
    
    lhs_results_root = os.path.join(RESULTS_FOLDER, "gathered")
    
    chesra1_results_file = os.path.join(lhs_results_root,"chesra1_results.csv")
    chesra2_results_file = os.path.join(lhs_results_root, "chesra2_results.csv")
    mart_results_file = os.path.join(lhs_results_root, "martonova3_results.csv")
    hao_results_file = os.path.join(lhs_results_root, "holzapfel-ogden_results.csv")

    chesra1_df = pd.read_csv(chesra1_results_file)
    chesra2_df = pd.read_csv(chesra2_results_file)
    mart_df = pd.read_csv(mart_results_file)
    hao_df = pd.read_csv(hao_results_file)

    opt_params_inverse_lhs = {}
    for scenario in ["ex_vivo_Klotz", "in_vivo_CMR"]:
        opt_params_inverse_lhs[scenario] = {}
        for efunc, efunc_df in zip(["chesra1", "chesra2", "martonova3", "holzapfel-ogden"], 
                                   [chesra1_df, chesra2_df, mart_df, hao_df]):
            opt_params_inverse_lhs[scenario][efunc] = efunc_df[list(filter(lambda x: "est_" in x, efunc_df.columns))]

    fig, axs = plt.subplots(2, 4, figsize=(12, 4    ), sharey="row")

    for i, scenario in enumerate(["ex_vivo_Klotz", "in_vivo_CMR"]):
        for j, efunc in enumerate(PARAM_ORDERS.keys()):
            plot_paramrange(efunc,
                            PARAM_ORDERS[efunc],
                            opt_params_inverse_lhs[scenario][efunc],
                            gt_params[scenario][efunc],
                            axs[i, j], 
                            EFUNC_COLORS[efunc],
                            title = None)

    # Custom legend handles
    box_patch = mpatches.Patch(facecolor=EFUNC_COLORS["chesra1"], edgecolor= "k", label="Estimate")
    line_patch = mlines.Line2D([], [], color="red", linestyle="--", linewidth=2, label="Benchmark value")

    axs[0, 0].legend(handles=[box_patch, line_patch], loc="best", fontsize = 10, frameon=False)

    fig.tight_layout(rect=[0, 0, 0.97, 1])

    labels = ["Ex vivo", "In vivo"]
    for i,label in enumerate(labels):
        row_bottom = axs[i, 0].get_position().y0
        row_top = axs[i, 0].get_position().y1
        row_mid = (row_bottom + row_top) / 2
        fig.text(0.97, row_mid, label, va='center', ha='left', rotation=90, fontsize=18, weight='bold')

    # Adjust layout
    plt.savefig("3D_Simulaton_Benchmark.png")
    plt.show()

if __name__ == "__main__":
    #gather_results()
    plot_results()