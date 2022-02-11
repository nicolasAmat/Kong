#!/usr/bin/env python3

"""
Kong: Koncurrent places Grinder

Input file format: .pnml / .nupn

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
__version__ = "2.0.0"

import argparse
import logging as log
import os
import subprocess
import sys
import tempfile
import time

from pt import PetriNet
from tfg import TFG
from utils import marking_parser


def main():
    """ Main Function.
    """
    # Arguments parser
    parser = argparse.ArgumentParser(description='Koncurrent places Grinder')

    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s 1.0.0',
                        help='show the version number and exit')

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='increase output verbosity')

    parser.add_argument('net',
                        metavar='filename',
                        type=str,
                        help='input Petri net (.pnml or .nupn format)')

    parser.add_argument('-m', '--marking',
                        action='store',
                        dest='marking',
                        type=str,
                        help='marking')

    group_reductions = parser.add_mutually_exclusive_group()

    group_reductions.add_argument('-sr', '--save-reduced-net',
                                  action='store_true',
                                  help='save the reduced net')

    group_reductions.add_argument('-rn', '--reduced-net',
                                  action='store',
                                  dest='reduced_net',
                                  type=str,
                                  help='specify reduced Petri net (.net format)')

    parser.add_argument('-t', '--time',
                        action='store_true',
                        help='show the computation time')

    parser.add_argument('-sf', '--show-formula',
                        action='store_true',
                        help='show the projected formula')

    parser.add_argument('-srr', '--show-reduction-ratio',
                        action='store_true',
                        help='show the reduction ratio')

    parser.add_argument('-se', '--show-equations',
                        action='store_true',
                        help='show the reduction equations')

    parser.add_argument('-dg', '--draw-graph',
                        action='store_true',
                        help='draw the Token Flow Graph')

    results = parser.parse_args()

    # Start time
    start_time = time.time()

    # Configure verbosity
    if results.verbose:
        log.basicConfig(format="%(message)s", level=log.DEBUG)
    else:
        log.basicConfig(format="%(message)s")

    # Set input file
    infile = results.net

    # Read initial Petri net
    log.info("> Read the input net")
    initial_net = PetriNet(infile, initial_net=True)
    infile = initial_net.filename

    # Manage reduced net
    f_reduced_net = None
    if results.reduced_net:
        reduced_net_filename = results.reduced_net
    else:
        log.info("> Reduce the input net")
        if results.save_reduced_net:
            reduced_net_filename = results.infile.replace('.pnml', '_reduced.net')
        else:
            f_reduced_net = tempfile.NamedTemporaryFile(suffix='.net')
            reduced_net_filename = f_reduced_net.name

        reduction_time = time.time()
        subprocess.run(["reduce", "-rg,redundant,compact,4ti2", "-redundant-limit", "650", "-redundant-time", "10", "-inv-limit", "1000", "-inv-time", "10", "-PNML", infile, reduced_net_filename], check=True)

        if results.time:
            print("# Reduction time:", time.time() - reduction_time)

    # Read reduced net
    log.info("> Read the reduced net")
    reduced_net = PetriNet(reduced_net_filename)

    # Show reduction ratio if option enabled
    if results.show_reduction_ratio:
        print("# Reduction ratio:", (1 - reduced_net.number_places / initial_net.number_places) * 100)

    # Build the Token Flow Graph
    log.info("> Build the Token Flow Graph")
    tfg = TFG(reduced_net_filename, initial_net, reduced_net, results.show_equations)

    # Draw graph if option enabled
    if results.draw_graph:
        tfg.draw_graph()

    # Read marking
    with open(results.marking) as fp:
        marking_str = fp.read()
    marking = marking_parser(marking_str)
    reduced_marking = tfg.marking_projection(marking)

    if reduced_marking is None:
        print("UNREACHABLE")
        sift_time = 0
    else:
        formula = '- (' + ' /\ '.join('{} = {}'.format(place, tokens) for place, tokens in reduced_marking.items()) + ')'
        
        if results.show_formula:
            print("# Projected formula:", formula)
        
        log.info("> Query to sift")
        sift_time = time.time()
        sift = subprocess.run(["sift", reduced_net_filename, "-f", formula], stdout=subprocess.PIPE, check=True)
        sift_time = time.time() - sift_time
        if "some state violates condition -f:" == sift.stdout.decode('utf-8').splitlines()[0]:
            print("REACHABLE")
        else:
            print("UNREACHABLE")

    # Show computation time
    if results.time:
        print("# Computation time: {} (sift: {})".format(time.time() - start_time, sift_time))

    # Close temporary files
    if not (results.save_reduced_net or results.reduced_net):
        f_reduced_net.close()


if __name__ == '__main__':
    sys.setrecursionlimit(10000)
    main()
    exit(0)
