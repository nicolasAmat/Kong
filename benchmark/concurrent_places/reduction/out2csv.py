#!/usr/bin/env python3

"""
Reduction Evaluation: .out to .csv script.
"""

import argparse
import csv
import glob
import os

import numpy as np


def reductions_converter(path_outputs):
    """ Convert `reductions/` files.
    """
    with open('../../reductions.csv', 'w') as csv_reductions:

        reductions_writer = csv.writer(csv_reductions)
        reductions_writer.writerow(['INSTANCE', 'RATIO_TFG', 'TIME_TFG', 'RATIO_REDUCE', 'TIME_REDUCE'])

        for outfile in glob.glob("{}/*.out".format(path_outputs)):

            # Get instance name
            instance = os.path.basename(outfile).replace('.out', '')

            # Get Kong data
            with open(outfile, 'r') as out:

                result = out.read().splitlines()

                ratio_tfg, time_tfg, ratio_reduce, time_reduce = np.nan, np.nan, np.nan, np.nan

                if result and len(result) == 4:
                    time_tfg = float(result[0].split(': ')[1])
                    ratio_tfg = float(result[1].split(': ')[1])
                    time_reduce = float(result[2].split(': ')[1])
                    ratio_reduce = float(result[3].split(': ')[1])
                else:
                    print("SKIPPED:", instance)

            # Write and show the corresponding row
            row = [instance, ratio_tfg, time_tfg, ratio_reduce, time_reduce]
            reductions_writer.writerow(row)
            print(' '.join(map(str, row)))


def main():
    """ Main function.
    """
    # Arguments parser
    parser = argparse.ArgumentParser(description='Reduction Evaluation: .out to .csv script')

    parser.add_argument('path_outputs',
                        metavar='outputs',
                        type=str,
                        help='path to outputs directory')

    results = parser.parse_args()

    reductions_converter(results.path_outputs)


if __name__ == "__main__":
    main()
    print("DONE")
    exit(0)
