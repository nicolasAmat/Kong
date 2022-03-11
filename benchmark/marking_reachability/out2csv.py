#!/usr/bin/env python3

"""
Marking Reachability Benchmark: out to .csv script.
"""

import argparse
import csv
import glob
import os

import numpy as np


def computations_converter(path_outputs):
    """ Convert `OUTPUTS/` files.
    """
    # Write computations data in `markings.csv`
    with open('../markings.csv'.format(path_outputs), 'w') as csv_computations:

        computations_writer = csv.writer(csv_computations)
        computations_writer.writerow(['INSTANCE', 'INDEX', 'TIME_KING', 'TIME_SIFT', 'RATIO', 'CORRECTNESS'])

        for query in set(filename.split('_')[0] for filename in glob.glob("{}/*.out".format(path_outputs))):

            # Get instance name and index
            instance, index = os.path.basename(query).rsplit('-', 1)
            time_king, time_sift = np.nan, np.nan
            correctness = True
            print(query)
            # Get King data
            with open("{}_king.out".format(query)) as out_king:
                king = out_king.read().splitlines()

                time_king, ratio = np.nan, np.nan
                correctness = True

                if len(king) > 1:
                    if 'Command exited with non-zero status 1' not in king[-3] or 'KeyError' in king[-4]:
                        ratio = float(king[0].split(': ')[1])
                        time_king = king[-2].split('user')
                        if len(time_king) > 1:
                            time_king = float(time_king[0])
                            correctness = king[1] == "REACHABLE"
                        else:
                            time_king = np.nan

            # Get Sift data
            with open("{}_sift.out".format(query)) as out_sift:
                sift = out_sift.read().splitlines()

                time_sift = np.nan

                if sift and  "Liste d'arguments trop longue" not in sift[0]:
                    time_sift = sift[-2].split('user')
                    if len(time_sift) > 1:
                        time_sift = float(time_sift[0])
                    else:
                        time_sift = np.nan

            # Write and show the corresponding row
            row = [instance, index, time_king, time_sift, ratio, correctness]
            computations_writer.writerow(row)
            print(' '.join(map(str, row)))


def main():
    """ Main function.
    """
    # Arguments parser
    parser = argparse.ArgumentParser(description='Marking Reachability Benchmark: .out to .csv script')

    parser.add_argument('path_outputs',
                        metavar='outputs',
                        type=str,
                        help='path to outputs directory')

    results = parser.parse_args()

    computations_converter(results.path_outputs)


if __name__ == "__main__":
    main()
    print("DONE")
    exit(0)
