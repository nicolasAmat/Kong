#!/usr/bin/env python3

"""
Concurrent places benchmark: .out to .csv script.
"""

import argparse
import csv
import glob
import os

import numpy as np


def complete_computations_converter(path_outputs):
    """ Convert `OUTPUTS/complete_computations/` files.
    """
    # Write computations data in `../csv/complete_concurrent_computations.csv`
    csv_path = os.path.join(os.path.dirname(__file__), '../csv/complete_concurrent_computations.csv')
    with open(csv_path, 'w') as csv_computations:

        computations_writer = csv.writer(csv_computations)
        computations_writer.writerow(['INSTANCE', 'RELATION_SIZE', 'CONCURRENT_PLACES', 'TIME_KONG', 'TIME_CAESAR', 'CORRECTNESS'])

        # Iterate over Kong `.out` files in `complete_computations/` subdirectory
        for kong_outfile in glob.glob("{}/complete_computations/*_kong.out".format(path_outputs)):

            # Check if the corresponding caesar `.out` file exists
            if os.path.exists(kong_outfile.replace('_kong', '_caesar')):
                caesar_outfile = kong_outfile.replace('_kong', '_caesar')
            else:
                print("SKIPPED:", kong_outfile.split('_kong.out')[0])
                continue

            # Get instance name
            instance = os.path.basename(kong_outfile).replace('_kong.out', '')
            relation_size, concurrent_places = 0, 0

            # Get Kong data
            with open(kong_outfile, 'r') as out_kong:

                kong = out_kong.read().splitlines()
                time_kong = np.nan
                matrix_kong = None

                if kong and '#' in kong[0]:
                    # Kong time
                    time_kong = float(kong[-2].split('user')[0])

                    # Kong matrix
                    matrix_kong = kong[2:-3]

                    # Get matrix information
                    relation_size = int(len(matrix_kong) * (len(matrix_kong) + 1) / 2)
                    for line in decompress_matrix(matrix_kong):
                        for concurrency in line:
                            if concurrency == '1':
                                concurrent_places += 1

            # Get Caesar data
            with open(caesar_outfile, 'r') as out_caesar:

                caesar = out_caesar.read().splitlines()
                time_caesar = np.nan
                matrix_caesar = None

                if caesar and len(caesar) > 1:
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

                        # Get matrix information
                        if not relation_size:
                            relation_size = int(len(matrix_caesar) * (len(matrix_caesar) + 1) / 2)
                            for line in decompress_matrix(matrix_caesar):
                                for concurrency in line:
                                    if concurrency == '1':
                                        concurrent_places += 1

                # Compute correctness
                correctness = (matrix_kong == matrix_caesar) or matrix_kong == None or matrix_caesar == None

            # Write and show the corresponding row
            row = [instance, relation_size, concurrent_places, time_kong, time_caesar, correctness]
            computations_writer.writerow(row)
            print(' '.join(map(str, row)))


def partial_computations_converter(path_outputs):
    """ Convert `OUTPUTS/partial_computations/` files.
    """
    # Write computations data in `../csv/partial_concurrent_computations.csv`
    csv_path = os.path.join(os.path.dirname(__file__), '../csv/partial_concurrent_computations.csv')
    with open(csv_path, 'w') as csv_computations:

        computations_writer = csv.writer(csv_computations)
        computations_writer.writerow(['INSTANCE', 'RELATION_SIZE', 'NUMBER_RELATIONS_KONG', 'CONCURRENT_PLACES_KONG', 'TIME_KONG', 'NUMBER_RELATIONS_CAESAR', 'CONCURRENT_PLACES_CAESAR', 'TIME_CAESAR', 'CORRECTNESS'])

        # Iterate over Kong `.out` files in `partial_computations/` subdirectory
        for kong_outfile in glob.glob("{}/partial_computations/*_kong.out".format(path_outputs)):

            # Check if the corresponding caesar `.out` file exists
            if os.path.exists(kong_outfile.replace('_kong', '_caesar')):
                caesar_outfile = kong_outfile.replace('_kong', '_caesar')
            else:
                continue

            # Get instance name
            instance = os.path.basename(kong_outfile).replace('_kong.out', '')

            # Get Kong data
            with open(kong_outfile) as out_kong:
                kong = out_kong.read().splitlines()
                time_kong = np.nan
                matrix_kong = None

                while kong and "caesar.bdd" in kong[0]:
                    kong.pop(0)

                if kong:
                    # Kong time
                    time_kong = float(kong[-2].split('user')[0])

                    # Kong matrix
                    matrix_kong = decompress_matrix(kong[2:-3])

            # Get caesar data
            with open(caesar_outfile) as out_caesar:

                caesar = out_caesar.read().splitlines()
                time_caesar = np.nan
                matrix_caesar = None

                if len(caesar) > 1:
                    time_data = caesar[-2].split('user')
                    if 'caesar.bdd' in caesar[0]:
                        caesar.pop(0)

                    if len(time_data) > 1 and caesar[0] in ['.', '0', '1']:
                        # Caesar time
                        time_caesar = float(time_data[0])
                        # Caesar matrix
                        matrix_caesar = decompress_matrix(caesar[:-2])

            # Get correctness and number of computed relations
            correctness = True
            relation_size, number_relations_kong, concurrent_places_kong, number_relations_caesar, concurrent_places_caesar = 0, 0, 0, 0, 0

            if matrix_kong and matrix_caesar:
                # Relation size (N*(N+1)/2))
                relation_size = int(len(matrix_kong) * (len(matrix_kong) + 1) / 2)
                for line_kong, line_caesar in zip(matrix_kong, matrix_caesar):
                    for relation_kong, relation_caesar in zip(line_kong, line_caesar):
                        # Increments known relations
                        if relation_kong != '.':
                            number_relations_kong += 1
                        if relation_kong == '1':
                            concurrent_places_kong += 1
                        if relation_caesar != '.':
                            number_relations_caesar += 1
                        if relation_caesar == '1':
                            concurrent_places_caesar +=1

                        # Check that both values are equal if they are known
                        if relation_kong != '.' and relation_caesar != '.' and relation_kong != relation_caesar:
                            correctness = False

            elif matrix_kong:
                relation_size = int(len(matrix_kong) * (len(matrix_kong) + 1) / 2)
                for line_kong in matrix_kong:
                    for relation_kong in line_kong:
                        # Increments known relations
                        if relation_kong != '.':
                            number_relations_kong += 1
                        if relation_kong == '1':
                            concurrent_places_kong += 1

            elif matrix_caesar:
                relation_size = int(len(matrix_caesar) * (len(matrix_caesar) + 1) / 2)
                for line_caesar in matrix_caesar:
                    for relation_caesar in line_caesar:
                        # Increments known relations
                        if relation_caesar != '.':
                            number_relations_caesar += 1
                        if relation_caesar == '1':
                            concurrent_places_caesar += 1

            # Write and show the corresponding row
            row = [instance, relation_size, number_relations_kong, concurrent_places_kong, time_kong, number_relations_caesar, concurrent_places_caesar, time_caesar, correctness]
            computations_writer.writerow(row)
            print(' '.join(map(str, row)))


def decompress_matrix(matrix):
    """ Decompress RLE matrix.
    """
    decompressed_matrix = []

    for line in matrix:
        if len(line) == 0:
            break

        new_line = []
        past_value = -1
        parse_multiplier = False
        multiplier = ""

        for value in line:           
            if value == '(':
                parse_multiplier = True
            elif value == ')':
                new_line.extend([past_value for _ in range(int(multiplier) - 1)])
                parse_multiplier = False
                multiplier = ""
            elif parse_multiplier:
                multiplier += value
            else:
                new_line.append(value)
                past_value = value

        decompressed_matrix.append(new_line)

    return decompressed_matrix


def main():
    """ Main function.
    """
    # Arguments parser
    parser = argparse.ArgumentParser(description='Concurrent places benchmark: .out to .csv script')

    parser.add_argument('path_outputs',
                        metavar='outputs',
                        type=str,
                        help='path to OUTPUTS/ directory')

    results = parser.parse_args()

    complete_computations_converter(results.path_outputs)
    partial_computations_converter(results.path_outputs)


if __name__ == "__main__":
    main()
    print("DONE")
    exit(0)
