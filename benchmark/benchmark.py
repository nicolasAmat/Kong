#!/usr/bin/env python3

"""
Benchmark script
"""

import argparse
import csv
import os
import subprocess
import sys
import tempfile
import time


def transition_rename(filename):
    """ Rename transitions in a .net file
        to avoir transitions and places to get equal names.
    """
    with open(filename, 'r') as file:
        filedata = file.read()

    filedata = filedata.replace('tr ', 'tr T_')

    with open(filename, 'w') as file:
        file.write(filedata)

def main():
    """ Main function.
    """
    # Arguments parser
    parser = argparse.ArgumentParser(description='Koncurrent Places Squasher Benchmark Script')
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s 1.0.0',
                        help="show the version number and exit")

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help="increase output verbosity")

    parser.add_argument('models_list',
                        metavar='list',
                        type=str,
                        help='list of models to analyze')

    parser.add_argument('models_directory',
                        metavar='directory',
                        type=str,
                        help='path to the models directory')

    parser.add_argument('-o', '--output',
                        action='store',
                        dest='output_file',
                        type=str,
                        default='results.csv',
                        help='path to output file (.csv format)')

    results = parser.parse_args()

    # Exit if PNML2NUPN not defined
    PNML2NUPN = os.getenv('PNML2NUPN')
    if not PNML2NUPN:
        sys.exit("Environment variable PNML2NUPN not defined!")

    with open(results.models_list, 'r') as models_list:
        with open(results.output_file, 'w', newline='') as csvfile:

            writer = csv.writer(csvfile)    
            writer.writerow(["Model", "Places number: initial net", "Places number: reduced net", "Places number: ratio", "Execution time: with reduction", "Execution time: without reduction", "Execution time: gain", "Correctness"])
        
            for model in models_list.readlines():
                model = model.strip()
                if model == '':
                    break

                model_path = results.models_directory + '/' + model

                # Places number: initial net
                number_places_initial = int(subprocess.run(["../pt.py", model_path], stdout=subprocess.PIPE).stdout.decode('utf-8').strip())
               
                # Places number: reduced net
                f_reduced_net = tempfile.NamedTemporaryFile(suffix='.net')
                subprocess.run(["reduce", "-rg,redundant,compact,convert,transitions", "-PNML", model_path, f_reduced_net.name])
                transition_rename(f_reduced_net.name)
                f_reduced_pnml = tempfile.NamedTemporaryFile(suffix='.pnml')
                subprocess.run(["ndrio", f_reduced_net.name, f_reduced_pnml.name])
                number_places_reduced = int(subprocess.run(["../pt.py", f_reduced_pnml.name], stdout=subprocess.PIPE).stdout.decode('utf-8').strip())
                f_reduced_net.close()
                f_reduced_pnml.close()

                # Ratio places
                ratio_places = (1 - number_places_reduced / number_places_initial) * 100

                # Run caesar.bdd (oracle)
                subprocess.run(["java", "-jar", PNML2NUPN, model_path], stdout=subprocess.DEVNULL)
                start = time.time()
                matrix_oracle = subprocess.run(["caesar.bdd", "-concurrent-places", model_path.replace('.pnml', '.nupn')], stdout=subprocess.PIPE).stdout.decode('utf-8').split('\n')
                computation_time_oracle = time.time() - start
                
                # Run Kong
                kong_output = subprocess.run(["../kong.py", '--time', model_path], stdout=subprocess.PIPE).stdout.decode('utf-8')
                matrix_kong = kong_output.split('\n')
                computation_time_kong = float(matrix_kong.pop(-2).split(': ')[1])

                # Ratio execution time
                ratio_execution_time = (1 - computation_time_kong / computation_time_oracle) * 100
                
                # Correctness checking
                correctness = matrix_oracle == matrix_kong
                
                # Write results to .csv file
                writer.writerow([model, number_places_initial, number_places_reduced, ratio_places, computation_time_oracle, computation_time_kong, ratio_execution_time, correctness])

                if results.verbose:
                    if correctness:
                        print("{}: Done".format(model))
                    else:
                        print("{}: Failure".format(model))

if __name__=='__main__':
    main()


