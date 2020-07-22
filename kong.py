#!/usr/bin/env python3

"""
Kong: Koncurrent Places Squasher

Input file format: .net

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

from concurrency_matrix import ConcurrencyMatrix
from pt import PetriNet
from e_abstraction import System, Relation

import argparse
import logging as log
import os
import subprocess
import sys
import tempfile


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
                        help='input Petri net (.pnml format)')

    parser.add_argument('--timeout',
                        action='store',
                        dest='timeout',
                        type=int,
                        default=60,
                        help='a limit on execution time')
    results = parser.parse_args()

    # Verbose option
    if results.verbose:
        log.basicConfig(format="%(message)s", level=log.DEBUG)
        stdout = None
    else:
        log.basicConfig(format="%(message)s")
        stdout = subprocess.DEVNULL

    # Read input net
    initial_net = PetriNet(results.infile)

    # Reduce input net
    f_reduced_net = tempfile.NamedTemporaryFile(suffix='.net')
    subprocess.run(["reduce", "-rg,redundant,compact,convert,transitions", "-PNML", results.infile, f_reduced_net.name])

    # Convert reduced net to .pnml format
    f_reduced_pnml = tempfile.NamedTemporaryFile(suffix='.pnml')
    subprocess.run(["ndrio", f_reduced_net.name, f_reduced_pnml.name])

    # Read reduced net
    reduced_net = PetriNet(f_reduced_pnml)

    # Read system of equations linking both nets
    system = System(f_reduced_net.name, initial_net.places, reduced_net.places) 

    # Convert reduced net to .nupn format
    PNML2NUPN = os.getenv('PNML2NUPN')
    if not PNML2NUPN:
        f_reduced_net.close()
        f_reduced_pnml.close()
        sys.exit("Environment variable PNML2NUPN not defined!")
    subprocess.run(["java", "-jar", PNML2NUPN, f_reduced_pnml.name], stdout=stdout)

    # Compute concurrency matrix of the reduced net
    matrix_reduced = subprocess.run(["caesar.bdd", "-concurrent-places", f_reduced_pnml.name.replace('.pnml', '.nupn')], stdout=subprocess.PIPE).stdout.decode('utf-8')
    concurrency_matrix = ConcurrencyMatrix(initial_net, reduced_net, system, matrix_reduced)

    # Close temporary files
    f_reduced_net.close()
    f_reduced_pnml.close()

if __name__ == '__main__':
    main()
    exit(0)