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
    with open('{}/reductions.csv'.format(path_outputs), 'w') as csv_reductions:
        reductions_writer = csv.writer(csv_reductions)
        reductions_writer.writerow(['INSTANCE', 'TIME', 'RATIO'])

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
                reductions_writer.writerow(row)
                print(' '.join(map(str, row)))


def complete_computations_converter(path_outputs):
    """ Convert `complete_computations/` files.
    """
    # Write computations data in `complete_computations.csv`
    with open('{}/complete_computations.csv'.format(path_outputs), 'w') as csv_computations:
        computations_writer = csv.writer(csv_computations)
        computations_writer.writerow(['INSTANCE', 'TIME_KONG', 'TIME_CAESAR', 'CORRECTNESS'])

        # Iterate over Kong `.out` files in `complete_computations/` subdirectory
        for kong_outfile in glob.glob("{}/complete_computations/*_Kong.out".format(path_outputs)):

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
                computations_writer.writerow(row)
                print(' '.join(map(str, row)))


def partial_computations_converter(path_outputs):
    """ Convert `partial_computations/` files.
    """
    # Write computations data in `partial_computations.csv`
    with open('{}/partial_computations.csv'.format(path_outputs), 'w') as csv_computations:
        computations_writer = csv.writer(csv_computations)
        computations_writer.writerow(['INSTANCE', 'NUMBER_RELATIONS_KONG', 'TIME_KONG', 'NUMBER_RELATIONS_CAESAR', 'TIME_CAESAR', 'CORRECTNESS'])

        # Iterate over Kong `.out` files in `computations/` subdirectory
        for kong_outfile in glob.glob("{}/partial_computations/*_Kong.out".format(path_outputs)):

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
                    if len(time_data) > 1:
                        # Caesar time
                        time_caesar = float(time_data[0])
                        # Caesar matrix
                        matrix_caesar = caesar[:-2]

            # Get correctness and number of computed relations
            correctness = True
            number_relations_kong, number_relations_caesar = 0, 0
            for line_kong, line_caesar in zip(matrix_kong, matrix_caesar):
                for relation_kong, relation_caesar in zip(line_kong, line_caesar):
                    # Increments known relations
                    if relation_kong != '.':
                        number_relations_kong += 1
                    if relation_caesar != '.':
                        number_relations_caesar += 1
                    # Check that both values are equal if they are known
                    if relation_kong != '.' and relation_caesar != '.' and relation_kong != relation_caesar:
                        correctness = False

                # Write and show the corresponding row
                row = [instance, number_relations_kong, time_kong, number_relations_caesar, time_caesar, correctness]
                computations_writer.writerow(row)
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
    complete_computations_converter(results.path_outputs)
    partial_computations_converter(results.path_output)


if __name__ == "__main__":
    main()
    print("DONE")
    exit(0)
