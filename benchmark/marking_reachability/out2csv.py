#!/usr/bin/env python3

"""
Marking reachability benchmark: out to .csv script.
"""

import argparse
import csv
import glob
import os

import numpy as np


def markings_converter(path_outputs):
    """ Convert `OUTPUTS/` files.
    """
    # Write computations data in `../csv/markings.csv`
    csv_path = os.path.join(os.path.dirname(__file__), '../csv/markings.csv')
    with open(csv_path, 'w') as csv_computations:

        computations_writer = csv.writer(csv_computations)
        computations_writer.writerow(['INSTANCE', 'INDEX', 'TIME_KONG', 'TIME_SIFT', 'RATIO', 'CORRECTNESS'])

        for query in set(filename.rpartition('_')[0] for filename in glob.glob("{}/*.out".format(path_outputs))):

            # Get instance name and index
            instance, index = os.path.basename(query).rsplit('-', 1)
            time_kong, time_sift = np.nan, np.nan
            correctness = True
            print(query)
            # Get Kong data
            with open("{}_kong.out".format(query)) as out_kong:
                kong = out_kong.read().splitlines()

                time_kong, ratio = np.nan, np.nan
                correctness = True

                if len(kong) > 1:
                    if 'Command exited with non-zero status 1' not in kong[-3] or 'KeyError' in kong[-4]:
                        ratio = float(kong[0].split(': ')[1])
                        time_kong = kong[-2].split('user')
                        if len(time_kong) > 1:
                            time_kong = float(time_kong[0])
                            correctness = kong[1] == "REACHABLE"
                        else:
                            time_kong = np.nan

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
            row = [instance, index, time_kong, time_sift, ratio, correctness]
            computations_writer.writerow(row)
            print(' '.join(map(str, row)))


def main():
    """ Main function.
    """
    # Arguments parser
    parser = argparse.ArgumentParser(description='Marking reachability benchmark: .out to .csv script')

    parser.add_argument('path_outputs',
                        metavar='outputs',
                        type=str,
                        help='path to OUTPUTS/ directory')

    results = parser.parse_args()

    markings_converter(results.path_outputs)


if __name__ == "__main__":
    main()
    print("DONE")
    exit(0)
