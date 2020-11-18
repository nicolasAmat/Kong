#!/usr/bin/env python3

"""
.out to .csv script.
"""

import argparse
import csv
import glob
import os

import numpy as np


def out_2_csv(path_outputs):
    """ Convert .out files to .csv files.
    """
    reduction_converter(path_outputs)
    computation_converter(path_outputs)


def reduction_converter(path_outputs):
    """ Convert `reductions/` files.
    """
    # Write reductions data in `reduction.csv`
    with open('{}/reductions.csv'.format(path_outputs), 'w') as csv_reduction:
        reduction_writer = csv.writer(csv_reduction)
        reduction_writer.writerow(['INSTANCE', 'TIME', 'RATIO'])

        # Iterate over files in `reductions/` subdirectory
        for instance in os.listdir("{}/reductions/".format(path_outputs)):
            with open("{}/reductions/{}".format(path_outputs, instance)) as out_reduction:
                reduction_data = out_reduction.read().splitlines()
   
                # Get data
                instance = instance.replace('.out', '')
                reduction_time = reduction_data[0].split(': ')[1]
                reduction_ratio = reduction_data[1].split(': ')[1]
                
                # Write and print the corresponding row
                row = [instance, reduction_time, reduction_ratio]
                reduction_writer.writerow(row)
                print(' '.join(map(str, row)))


def computation_converter(path_outputs):
    """ Convert `reductions/` files.
    """
    # Write computations data in `computation.csv`
    with open('{}/reductions.csv'.format(path_outputs), 'w') as csv_computation:
        computation_writer = csv.writer(csv_computation)
        computation_writer.writerow(['INSTANCE', 'TIME_KONG', 'TIME_CAESAR', 'CORRECTNESS'])

        # Iterate over files in `computations/` subdirectory
        for kong_outfile in glob.glob("{}/computations/*_Kong.out".format(path_outputs)):

            # Get instance name
            instance = os.path.basename(kong_outfile).replace('_Kong.out', '')

            # Get Kong data
            with open(kong_outfile) as out_kong:
                kong = out_kong.read().splitlines()
                if kong:
                    time_kong = round(float(kong[-1].split(': ')[1]), 2)
                    matrix_kong = kong[:-1]
                else:
                    time_kong = np.nan
                    matrix_kong = None

            # Get caesar data
            caesar_outfile = kong_outfile.replace('_Kong', '_caesar') 
            with open(caesar_outfile) as out_caesar:
                caesar = out_caesar.read().splitlines()
                if caesar:
                    time_caesar = caesar[-2].split('user')[0]
                    matrix_caesar = caesar[:-2]
                else:
                    time_caesar = np.nan
                    matrix_caesar = None

            # Compute correctness
            correctness = matrix_kong == matrix_caesar
            
            # Write and print the corresponding row
            row = [instance, time_kong, time_caesar, correctness]
            computation_writer.writerow(row)
            print(' '.join(map(str, row)))


def main():
    """ Main function.
    """
    # Arguments parser
    parser = argparse.ArgumentParser(description='Kong Benchmark Script')

    parser.add_argument('path_outputs',
                        metavar='outputs',
                        type=str,
                        help='path to outputs directory')

    results = parser.parse_args()

    out_2_csv(results.path_outputs)


if __name__ == "__main__":
    main()
    print("DONE")
    exit(0)
