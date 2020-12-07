#!/usr/bin/env python3

"""
.out to .csv script.
"""

import argparse
import csv
import glob
import math
import os

import numpy as np


def reductions_converter(path_outputs):
    """ Convert `reductions/` files.
    """
    # Write reductions data in `reductions.csv`
    with open('{}/reductions.csv'.format(path_outputs), 'w') as csv_reduction:
        reduction_writer = csv.writer(csv_reduction)
        reduction_writer.writerow(['INSTANCE', 'TIME', 'RATIO'])

        # Iterate over `.out` files in `reductions/` subdirectory
        for instance in os.listdir("{}/reductions/".format(path_outputs)):
            with open("{}/reductions/{}".format(path_outputs, instance)) as out_reduction:
                # Get data
                reduction_data = out_reduction.read().splitlines()
                # Instance name
                instance = instance.replace('.out', '')
                # Round up reduction time (2 decimals)
                reduction_time = math.ceil(float(reduction_data[0].split(': ')[1]) * 100) / 100
                # Round up reduction time (2 decimals)
                reduction_ratio = math.ceil(float(reduction_data[1].split(': ')[1]) * 100) / 100

                # Write and show the corresponding row
                row = [instance, reduction_time, reduction_ratio]
                reduction_writer.writerow(row)
                print(' '.join(map(str, row)))


def computations_converter(path_outputs):
    """ Convert `computations/` files.
    """
    # Write computations data in `computations.csv`
    with open('{}/computations.csv'.format(path_outputs), 'w') as csv_computation:
        computation_writer = csv.writer(csv_computation)
        computation_writer.writerow(['INSTANCE', 'TIME_KONG', 'TIME_CAESAR', 'CORRECTNESS'])

        # Iterate over Kong `.out` files in `computations/` subdirectory
        for kong_outfile in glob.glob("{}/computations/*_Kong.out".format(path_outputs)):

            # Check if the corresponding caesar `.out` file exists
            if os.path.exists(kong_outfile.replace('_Kong', '_caesar')):
                caesar_outfile = kong_outfile.replace('_Kong', '_caesar')
            else:
                continue

            # Get instance name
            instance = os.path.basename(kong_outfile).replace('_Kong.out', '')

            # Get Kong data
            with open(kong_outfile) as out_kong:
                kong = out_kong.read().splitlines()
                time_kong = np.nan
                matrix_kong = None
                if kong:
                    # Round up reduction time (2 decimals)
                    time_kong = math.ceil(float(kong[-1].split(': ')[1]) * 100) / 100
                    # Kong matrix
                    matrix_kong = kong[:-1]

            # Get caesar data
            with open(caesar_outfile) as out_caesar:
                caesar = out_caesar.read().splitlines()
                time_caesar = np.nan
                matrix_caesar = None
                if caesar:
                    time_data = caesar[-2].split('user')
                    # Check matrix completeness
                    complete = True
                    for line in caesar[:-2]:
                        if '.' in line or len(line.split(' ')) > 1:
                            complete = False
                            break
                    if len(time_data) > 1 and complete:
                        # Caesar time
                        time_caesar = float(time_data[0])
                        # Caesar matrix
                        matrix_caesar = caesar[:-2]

                # Compute correctness
                correctness = (matrix_kong == matrix_caesar) or matrix_kong == None or matrix_caesar == None

                # Write and show the corresponding row
                row = [instance, time_kong, time_caesar, correctness]
                computation_writer.writerow(row)
                print(' '.join(map(str, row)))


def main():
    """ Main function.
    """
    # Arguments parser
    parser = argparse.ArgumentParser(description='.out to .csv script')

    parser.add_argument('path_outputs',
                        metavar='outputs',
                        type=str,
                        help='path to outputs directory')

    results = parser.parse_args()

    reductions_converter(results.path_outputs)
    computations_converter(results.path_outputs)


if __name__ == "__main__":
    main()
    print("DONE")
    exit(0)
