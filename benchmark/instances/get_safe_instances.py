#!/usr/bin/env python3

"""
Generate the list of safe nets among the INPUTS/ directory (official MCC models).
"""

import argparse
import os
import xml.etree.ElementTree as ET


def main():

    parser = argparse.ArgumentParser(description='Generate the list of safe nets among the INPUTS directory')

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
    nb_safe, nb_total = 0, 0

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
                colored = 'TRUE' in content_file.read()
            if colored:
                continue

            # Skip if there is no GenericPropertiesVerdict.xml file
            if not os.path.isfile(instance + '/GenericPropertiesVerdict.xml'):
                continue 

            # Get tags from the GenericPropertiesVerdict.xml file
            root_node = ET.parse(instance + '/GenericPropertiesVerdict.xml').getroot()
            for tag in root_node.findall('verdict'):
                # Get SAFE tag
                if tag.get('reference') == 'SAFE':
                    safe = tag.get('value') == 'true'
                # Get ORDINARY tag
                if tag.get('reference') == 'ORDINARY':
                    ordinary = tag.get('value') == 'true'

            # Skip if the instance is not safe or not ordinary
            if not (safe and ordinary):
                continue

            # Increment the number of safe instances
            nb_safe += 1

            # Print the instance        
            instance_name = os.path.basename(instance)
            fp_list.write(instance_name)
            print(instance_name)

    print('################################################################################')
    print("# TOTAL :", nb_total)
    print("# SAFE  :", nb_safe)


if __name__=='__main__':
    main()
