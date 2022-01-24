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
from shutil import which

from pt import PetriNet
from tfg import TFG
from utils import matrix_from_str, show_matrix


def exit_helper(results, f_pnml, f_net, f_reduced_net, f_reduced_pnml):
    """ Close temporary files.
    """
    if f_pnml is not None:
        f_pnml.close()

    if f_net is not None:
        f_net.close()

    if not (results.save_reduced or results.reduced_net):
        f_reduced_net.close()

    f_reduced_pnml.close()


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

    parser.add_argument('infile',
                        metavar='filename',
                        type=str,
                        help='input Petri net (.pnml or .nupn format)')

    group_reductions = parser.add_mutually_exclusive_group()

    parser.add_argument('-dp', '--dead-places',
                        action='store_true',
                        help='only compute dead places')

    parser.add_argument('-sk', '--shrink',
                        action='store_true',
                        help='use Shrink tool')

    group_reductions.add_argument('-sr', '--save-reduced',
                                  action='store_true',
                                  help='save the reduced net')

    group_reductions.add_argument('-r', '--reduced',
                                  action='store',
                                  dest='reduced_net',
                                  type=str,
                                  help='reduced Petri Net (.net format)')

    parser.add_argument('-nu', '--no-units',
                        action='store_true',
                        help='disable units propagation')

    parser.add_argument('-nr', '--no-rle',
                        action='store_true',
                        help='disable run-length encoding (RLE)')

    parser.add_argument('-pl', '--place-names',
                        action='store_true',
                        help='show place names')

    parser.add_argument('-t', '--time',
                        action='store_true',
                        help='show the computation time')

    parser.add_argument('-sn', '--show-nupns',
                        action='store_true',
                        help='show the NUPNs')

    parser.add_argument('-srr', '--show-reduction-ratio',
                        action='store_true',
                        help='show the reduction ratio')

    parser.add_argument('-se', '--show-equations',
                        action='store_true',
                        help='show the reduction equations')

    parser.add_argument('-srm', '--show-reduced-matrix',
                        action='store_true',
                        help='show the reduced matrix')

    parser.add_argument('-dg', '--draw-graph',
                        action='store_true',
                        help='draw the Token Flow Graph')

    parser.add_argument('--bdd-timeout',
                        action='store',
                        dest='bdd_timeout',
                        type=str,
                        help='set the time limit for marking graph exploration (caesar.bdd)')

    parser.add_argument('--bdd-iterations',
                        action='store',
                        dest='bdd_iterations',
                        type=str,
                        help='set the limit for number of iterations for marking graph exploration (caesar.bdd)')

    results = parser.parse_args()

    # Configure verbosity
    if results.verbose:
        log.basicConfig(format="%(message)s", level=log.DEBUG)
        stdout = None
    else:
        log.basicConfig(format="%(message)s")
        stdout = subprocess.DEVNULL

    # Convert .nupn to .pnml
    f_pnml, f_net = None, None
    if results.infile.lower().endswith('.nupn'):
        log.info("> Convert '.nupn' to '.pnml'")
        f_pnml = tempfile.NamedTemporaryFile(suffix='.pnml')
        subprocess.run(["caesar.bdd", "-pnml", results.infile], stdout=f_pnml, check=True)
        results.infile = f_pnml.name

    # Read initial Petri net
    log.info("> Read the input net")
    initial_net = PetriNet(results.infile, initial_net=True)
    results.infile = initial_net.filename

    # Show initial NUPN if option enabled
    if results.show_nupns:
        print("# Initial NUPN")
        print(initial_net.NUPN)

    # Manage reduced net
    f_reduced_net = None
    if results.reduced_net:
        reduced_net_filename = results.reduced_net
    else:
        log.info("> Reduce the input net")
        if results.save_reduced:
            reduced_net_filename = results.infile.replace('.pnml', '_reduced.net')
        else:
            f_reduced_net = tempfile.NamedTemporaryFile(suffix='.net')
            reduced_net_filename = f_reduced_net.name

        start_time = time.time()

        if not results.shrink and which("reduce") is not None:
            subprocess.run(["reduce", "-rg,redundant,compact,4ti2", "-redundant-limit", "650", "-redundant-time", "10", "-inv-limit", "1000", "-inv-time", "10", "-PNML", results.infile, reduced_net_filename], check=True)
        else:
            subprocess.run(["shrink", "--equations", "--clean", "--redundant", "--compact", "--struct", "-i", results.infile, "-o", reduced_net_filename], check=True)

        if results.time:
            print("# Reduction time:", time.time() - start_time)

    # Convert reduced net to .pnml format
    log.info("> Convert the reduced net to '.pnml' format")
    f_reduced_pnml = tempfile.NamedTemporaryFile(suffix='.pnml')
    subprocess.run(["ndrio", reduced_net_filename, f_reduced_pnml.name], check=True)

    # Read reduced net
    log.info("> Read the reduced net")
    reduced_net = PetriNet(f_reduced_pnml)

    # Show reduction ratio if option enabled
    if results.show_reduction_ratio:
        print("# Reduction ratio:", (1 - reduced_net.number_places / initial_net.number_places) * 100)

    # Build the Token Flow Graph
    log.info("> Build the Token Flow Graph")
    tfg = TFG(reduced_net_filename, initial_net, reduced_net, results.show_equations)

    if reduced_net.places:
        # Project units of the initial net to the reduced net if there is a NUPN decomposition
        if not results.no_units and initial_net.NUPN:
            log.info("> Project units")
            tfg.units_projection()
            reduced_net.NUPN.write_toolspecific_pnml(f_reduced_pnml.name)

        # Show initial NUPN if option enabled
        if results.show_nupns:
            print("# Reduced NUPN")
            print(reduced_net.NUPN)

        # Convert reduced net to .nupn format
        log.info("> Convert the reduced Petri net to '.nupn' format")
        reduced_nupn = f_reduced_pnml.name.replace('.pnml', '.nupn')
        subprocess.run(["ndrio", f_reduced_pnml.name, reduced_nupn], stdout=stdout, check=True)

        # Update places order
        reduced_net.update_order_from_nupn(reduced_nupn)

        # Start time
        start_time = time.time()

        # Set the time limit for marking graph exploration
        if results.bdd_timeout:
            os.environ['CAESAR_BDD_TIMEOUT'] = results.bdd_timeout
            log.info("> Set environment variable CAESAR_BDD_TIMEOUT to `%s'", os.environ['CAESAR_BDD_TIMEOUT'])
        elif os.getenv('CAESAR_BDD_TIMEOUT'):
            log.warning("> Environment variable CAESAR_BDD_TIMEOUT is already set to `%s'", os.environ['CAESAR_BDD_TIMEOUT'])

        # Set the limit for the number of iterations for marking graph exploration
        if results.bdd_iterations:
            os.environ['CAESAR_BDD_ITERATIONS'] = results.bdd_iterations
            log.info("> Set environment variable CAESAR_BDD_ITERATIONS to `%s'", os.environ['CAESAR_BDD_ITERATIONS'])
        elif os.getenv('CAESAR_BDD_ITERATIONS'):
            log.warning("> Environment variable CAESAR_BDD_ITERATIONS is already set to `%s'", os.environ['CAESAR_BDD_ITERATIONS'])

        # Compute concurrency matrix of the reduced net
        log.info("> Compute the concurrency matrix of the reduced net")
        caesar_bdd_data = subprocess.run(["caesar.bdd", "-concurrent-places", reduced_nupn], stdout=subprocess.PIPE)
        caesar_bdd_time = time.time() - start_time
        assert caesar_bdd_data.returncode in (0, 5), "Unexpected error while computing the concurrency matrix of the reduced net"
        reduced_matrix, complete_matrix = matrix_from_str(caesar_bdd_data.stdout.decode('utf-8'))

    else:
        # Fully reducible net case
        start_time = time.time()
        reduced_matrix = ''
        complete_matrix = True
        caesar_bdd_time = 0

    # Show the reduced matrix if enabled
    if results.show_reduced_matrix:
        print("# Reduced concurrency matrix")
        show_matrix(reduced_matrix, reduced_net, results.no_rle, results.place_names)

    # Draw graph if option enabled
    if results.draw_graph:
        tfg.draw_graph()

    # Change of Basis
    log.info("> Change of dimension")
    matrix = tfg.matrix(reduced_matrix, complete_matrix)
    show_matrix(matrix, initial_net, results.no_rle, results.place_names)

    # Show computation time
    if results.time:
        computation_time = time.time() - start_time
        change_basis_time = computation_time - caesar_bdd_time
        print("# Computation time: {} (Caesar.bdd: {} + Change of Dimension: {})".format(computation_time, caesar_bdd_time, change_basis_time))

    exit_helper(results, f_pnml, f_net, f_reduced_net, f_reduced_pnml)


if __name__ == '__main__':
    sys.setrecursionlimit(10000)
    main()
    exit(0)
