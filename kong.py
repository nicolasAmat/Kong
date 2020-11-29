#!/usr/bin/env python3

"""
Kong: Koncurrent Places Squasher

Input file format: .pnml

This file is part of Kong.

Kong is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Kong is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Kong. If not, see <https://www.gnu.org/licenses/>.
"""

__author__ = "Nicolas AMAT, LAAS-CNRS"
__contact__ = "namat@laas.fr"
__license__ = "GPLv3"
__version__ = "1.0.0"

import argparse
import logging as log
import os
import subprocess
import sys
import tempfile
import time

from concurrency_matrix import ConcurrencyMatrix
from pt import PetriNet


def transition_renamer(filename):
    """ Rename transitions in a .net file
        to avoid similar names between transitions and places.
    """
    with open(filename, 'r') as file:
        filedata = file.read()

    filedata = filedata.replace('tr ', 'tr T_').replace('T_{','{T_')

    with open(filename, 'w') as file:
        file.write(filedata)

def main():
    """ Main Function.
    """
    # Arguments parser
    parser = argparse.ArgumentParser(description='Koncurrent Places Squasher')
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s 1.0.0',
                        help="show the version number and exit")

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help="increase output verbosity")

    parser.add_argument('infile',
                        metavar='filename',
                        type=str,
                        help="input Petri net (.pnml format)")

    group_reductions = parser.add_mutually_exclusive_group()

    group_reductions.add_argument('--save-reduced', '-sr',
                                    action='store_true',
                                    help="save the reduced net")

    group_reductions.add_argument('--reduced', '-r',
                                    action='store',
                                    dest='reduced_net',
                                    type=str,
                                    help='reduced Petri Net (.net format)')

    parser.add_argument('-pl', '--place_names',
                        action='store_true',
                        help="display place names")

    parser.add_argument('-t', '--time',
                        action='store_true',
                        help="show computation time")

    parser.add_argument('--reduction-ratio',
                        action='store_true',
                        help='show the reduction ratio')

    results = parser.parse_args()

    # Verbose option
    if results.verbose:
        log.basicConfig(format="%(message)s", level=log.DEBUG)
        stdout = None
    else:
        log.basicConfig(format="%(message)s")
        stdout = subprocess.DEVNULL

    # Read input net
    log.info("> Read the input Petri net")
    initial_net = PetriNet(results.infile)

    # Manage reduced net
    if results.reduced_net:
        reduced_net_filename = results.reduced_net
    else:
        log.info("> Reduce the input Petri net")
        if results.save_reduced:
            reduced_net_filename = results.infile.replace('.pnml', '_reduced.net')
        else:
            f_reduced_net = tempfile.NamedTemporaryFile(suffix='.net')
            reduced_net_filename = f_reduced_net.name
        start_time = time.time()
        subprocess.run(["reduce", "-rg,redundant,compact,mg,4ti2", "-redundant-limit", "650", "-redundant-time", "10", "-inv-limit", "1000", "-inv-time", "10", "-PNML", results.infile, reduced_net_filename])
        if results.time:
            print("# Reduction time:", time.time() - start_time)
    if not results.reduced_net:
        transition_renamer(reduced_net_filename)

    # Convert reduced net to .pnml format
    log.info("> Convert the reduced Petri net to '.pnml' format")
    f_reduced_pnml = tempfile.NamedTemporaryFile(suffix='.pnml')
    subprocess.run(["ndrio", reduced_net_filename, f_reduced_pnml.name])

    # Read reduced net
    log.info("> Read the reduced Petri net")
    reduced_net = PetriNet(f_reduced_pnml)

    # Display reduction ratio if enabled
    if results.reduction_ratio:
        print("# Reduction ratio:", (1 - reduced_net.number_places / initial_net.number_places) * 100)
        # Close temporary files
        if not (results.save_reduced or results.reduced_net):
            f_reduced_net.close()
        f_reduced_pnml.close()
        return

    start_time = time.time()

    if reduced_net.places:
        # Convert reduced net to .nupn format
        log.info("> Convert the reduced Petri net to '.nupn' format")
        PNML2NUPN = os.getenv('PNML2NUPN')
        if not PNML2NUPN:
            if not (results.save_reduced or results.reduced_net):
                f_reduced_net.close()
            f_reduced_pnml.close()
            sys.exit("Environment variable PNML2NUPN not defined!")
        subprocess.run(["java", "-jar", PNML2NUPN, f_reduced_pnml.name], stdout=stdout)

        start_time = time.time()

        # Compute concurrency matrix of the reduced net
        log.info("> Compute the concurrency matrix of the reduced Petri net")
        matrix_reduced = subprocess.run(["caesar.bdd", "-concurrent-places", f_reduced_pnml.name.replace('.pnml', '.nupn')], stdout=subprocess.PIPE).stdout.decode('utf-8')
    else:
        matrix_reduced = ''

    # Compute the concurrency matrix of the initial net using the system of equations and the concurrency matrix from the reduced net
    log.info("> Change of basis")
    concurrency_matrix = ConcurrencyMatrix(initial_net, reduced_net, reduced_net_filename, matrix_reduced, results.place_names)

    # Show computation time
    if results.time:
        print("# Computation time:", time.time() - start_time)

    # Close temporary files
    if not (results.save_reduced or results.reduced_net):
        f_reduced_net.close()
    f_reduced_pnml.close()

if __name__ == '__main__':
    main()
    exit(0)
