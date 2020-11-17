#!/usr/bin/env python3

"""
.out to .csv script.
"""

import argparse
import csv
import glob
import os
import shutil

import numpy as np
import pandas as pd


def out_2_csv(path_outputs):
    """ Convert .out files to .csv files.
    """
    reduction_converter(path_outputs)


def reduction_converter(path_outputs):
    """ Convert `reductions/` files.
    """
    # Write reduction data in `reduction.csv`
    with open('{}/reductions.csv'.format(path_outputs), 'w') as csv_reduction:
        reduction_writer = csv.writer(csv_reduction)
        reduction_writer.writerow(['INSTANCE', 'TIME', 'RATIO'])
        
        for instance in os.listdir("{}/reductions/".format(path_outputs)):
            with open("{}/reductions/{}".format(path_outputs, instance)) as out_reduction:
                reduction_data = out_reduction.readlines()
                
                instance = instance.replace('.out', '.pnml')
                reduction_time = reduction_data[0].rstrip().split(': ')[1]
                reduction_ratio = reduction_data[1].rstrip().split(': ')[1]
                reduction_data = [instance, reduction_time, reduction_ratio]
                
                reduction_writer.writerow(reduction_data)
                print(' '.join(map(str, reduction_data)))


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
