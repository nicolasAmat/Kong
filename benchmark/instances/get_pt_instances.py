#!/usr/bin/env python3

"""
Generate the list of colorblind nets among the INPUTS/ directory (official MCC models).
"""

import argparse
import os
import xml.etree.ElementTree as ET


def main():

    parser = argparse.ArgumentParser(description='Generate the list of colorblind nets among the INPUTS directory')

    parser.add_argument('path_inputs',
                        metavar='INPUTS',
                        type=str,
                        help='path to the INPUTS/ directory')

    parser.add_argument('path_list',
                        metavar='list',
                        type=str,
                        help='path to the generated list')

    results = parser.parse_args()

    # Initalize the counting variables
    nb_pt, nb_total = 0, 0

    with open(results.path_list, 'w') as fp_list:

        # Iterate over subdirectories
        for instance, _, _ in os.walk(results.path_inputs):

            # Skip the root directory
            if instance == results.path_inputs:
                continue

            # Increment the number of instances
            nb_total += 1

            # Skip colored instances
            with open(instance + '/iscolored', 'r') as content_file:
                if 'TRUE' in content_file.read():
                    continue

            # Increment the number of safe instances
            nb_pt += 1

            # Print the instance        
            instance_name = os.path.basename(instance)
            fp_list.write(instance_name + '\n')
            print(instance_name)

    print('################################################################################')
    print("# PT    :", nb_pt)
    print("# TOTAL :", nb_total)


if __name__=='__main__':
    main()
