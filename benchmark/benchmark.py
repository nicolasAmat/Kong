#!/usr/bin/env python3

"""
Benchmarking Script

This file is part of Kong.

Kong is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Kong is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Kong. If not, see <https://www.gnu.org/licenses/>.
"""

__author__ = "Nicolas AMAT, LAAS-CNRS"
__contact__ = "namat@laas.fr"
__license__ = "GPLv3"
__version__ = "1.0.0"

import argparse
import csv
import os
import subprocess
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
    results = parser.parse_args()

    with open(results.models_list, 'r') as models_list:
        with open('results.csv', 'w', newline='') as csvfile:

            writer = csv.writer(csvfile)    
            writer.writerow(["Model", "Places number: initial net", "Places number: reduced net", "Places number: ratio", "Execution time: initial net", "Execution time: reduced net", "Execution time: ratio", "Correct"])
        
            for model in models_list.readlines():
                model = model.strip()
                model_path = results.models_directory + '/' + model

                # Places number: initial net
                number_places_1 = int(subprocess.run(["../pt.py", model_path], stdout=subprocess.PIPE).stdout.decode('utf-8').strip())
               
                # Places number: reduced net
                f_reduced_net = tempfile.NamedTemporaryFile(suffix='.net')
                subprocess.run(["reduce", "-rg,redundant,compact,convert,transitions", "-PNML", model_path, f_reduced_net.name])
                transition_rename(f_reduced_net.name)
                f_reduced_pnml = tempfile.NamedTemporaryFile(suffix='.pnml')
                subprocess.run(["ndrio", f_reduced_net.name, f_reduced_pnml.name])
                number_places_2 = int(subprocess.run(["../pt.py", f_reduced_pnml.name], stdout=subprocess.PIPE).stdout.decode('utf-8').strip())
                f_reduced_net.close()
                f_reduced_pnml.close()

                # Ratio places
                ratio_places = number_places_2 / number_places_1

                # Run caesar.bdd (oracle)
                PNML2NUPN = os.getenv('PNML2NUPN')
                subprocess.run(["java", "-jar", PNML2NUPN, model_path], stdout=subprocess.DEVNULL)
                start = time.time()
                matrix_1 = subprocess.run(["caesar.bdd", "-concurrent-places", model_path.replace('.pnml', '.nupn')], stdout=subprocess.PIPE).stdout.decode('utf-8')
                elapsed_1 = time.time() - start
                
                # Run Kong
                start = time.time()
                matrix_2 = subprocess.run(["../kong.py", model_path], stdout=subprocess.PIPE).stdout.decode('utf-8')
                elapsed_2 = time.time() - start

                # Ratio execution time
                ratio_execution_time = elapsed_2 / elapsed_1

                # Correctness checking
                correctness = matrix_1.split("\n") == matrix_2.split("\n")
                
                # Write results to .csv file
                writer.writerow([model, number_places_1, number_places_2, ratio_places, elapsed_1, elapsed_2, ratio_execution_time, correctness])

                if results.verbose:
                    if correctness:
                        print("{}: Done".format(model))
                    else:
                        print("{}: Failure".format(model))

if __name__=='__main__':
    main()


