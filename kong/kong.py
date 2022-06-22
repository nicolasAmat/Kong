#!/usr/bin/env python3

"""
Kong: Koncurrent places Grinder

Input file format: .pnml / .nupn (concurrent and dead places)
                   .pnml / .net  (marking reachability)

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
from utils import marking_parser, matrix_from_str, show_matrix


def conc(args):
    """ Concurrent places computation wrapper.
    """
    conc_dead(args, "concurrency matrix", "-concurrent-places")


def dead(args):
    """ Dead places computation wrapper.
    """
    conc_dead(args, "dead places vector", "-dead-places")


def conc_dead(args, computation, caesar_option):
    """ Compute concurrent and/or dead places.
    """
    # Configure verbosity
    if args.verbose:
        log.basicConfig(format="%(message)s", level=log.DEBUG)
        stdout = None
    else:
        log.basicConfig(format="%(message)s")
        stdout = subprocess.DEVNULL

    # Set input file
    infile = args.infile

    # Convert .nupn to .pnml
    f_pnml, f_net = None, None
    if infile.lower().endswith('.nupn'):
        log.info("> Convert '.nupn' to '.pnml'")
        f_pnml = tempfile.NamedTemporaryFile(suffix='.pnml')
        subprocess.run(["caesar.bdd", "-pnml", infile], stdout=f_pnml, check=True)
        infile = f_pnml.name

    # Read initial Petri net
    log.info("> Read the input net")
    initial_net = PetriNet(infile, initial_net=True)
    infile = initial_net.filename

    # Show initial NUPN if option enabled
    if args.show_nupns:
        print("# Initial NUPN")
        print(initial_net.NUPN)

    # Manage reduced net
    f_reduced_net = None
    if args.reduced_net:
        reduced_net_filename = args.reduced_net
    else:
        log.info("> Reduce the input net")
        if args.save_reduced_net:
            reduced_net_filename = args.infile.replace('.pnml', '_reduced.net')
        else:
            f_reduced_net = tempfile.NamedTemporaryFile(suffix='.net')
            reduced_net_filename = f_reduced_net.name

        start_time = time.time()

        if not args.shrink and which("reduce") is not None:
            subprocess.run(["reduce", "-rg,redundant,compact,4ti2", "-redundant-limit", "650", "-redundant-time", "10", "-inv-limit", "1000", "-inv-time", "10", "-PNML", infile, reduced_net_filename], check=True)
        else:
            subprocess.run(["shrink", "--equations", "--clean", "--redundant", "--compact", "-i", infile, "-o", reduced_net_filename], check=True)

        if args.time:
            print("# Reduction time:", time.time() - start_time)

    # Convert reduced net to .pnml format
    log.info("> Convert the reduced net to '.pnml' format")
    f_reduced_pnml = tempfile.NamedTemporaryFile(suffix='.pnml')
    subprocess.run(["ndrio", reduced_net_filename, f_reduced_pnml.name], check=True)

    # Read reduced net
    log.info("> Read the reduced net")
    reduced_net = PetriNet(f_reduced_pnml.name)

    # Show reduction ratio if option enabled
    if args.show_reduction_ratio:
        print("# Reduction ratio:", (1 - reduced_net.number_places / initial_net.number_places) * 100)

    # Build the Token Flow Graph
    log.info("> Build the Token Flow Graph")
    tfg = TFG(reduced_net_filename, initial_net, reduced_net, args.show_equations)

    if reduced_net.places:
        # Project units of the initial net to the reduced net if there is a NUPN decomposition
        if not args.no_units and initial_net.NUPN:
            log.info("> Project units")
            tfg.units_projection()
            reduced_net.NUPN.write_toolspecific_pnml(f_reduced_pnml.name)

        # Show initial NUPN if option enabled
        if args.show_nupns:
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
        if args.bdd_timeout:
            os.environ['CAESAR_BDD_TIMEOUT'] = str(args.bdd_timeout)
            log.info("> Set environment variable CAESAR_BDD_TIMEOUT to `%s'", os.environ['CAESAR_BDD_TIMEOUT'])
        elif os.getenv('CAESAR_BDD_TIMEOUT'):
            log.warning("> Environment variable CAESAR_BDD_TIMEOUT is already set to `%s'", os.environ['CAESAR_BDD_TIMEOUT'])

        # Set the limit for the number of iterations for marking graph exploration
        if args.bdd_iterations:
            os.environ['CAESAR_BDD_ITERATIONS'] = str(args.bdd_iterations)
            log.info("> Set environment variable CAESAR_BDD_ITERATIONS to `%s'", os.environ['CAESAR_BDD_ITERATIONS'])
        elif os.getenv('CAESAR_BDD_ITERATIONS'):
            log.warning("> Environment variable CAESAR_BDD_ITERATIONS is already set to `%s'", os.environ['CAESAR_BDD_ITERATIONS'])

        if not args.reduced_result:
            # Compute concurrency matrix / dead places vector of the reduced net
            log.info("> Compute the {} of the reduced net".format(computation))
            caesar_bdd_data = subprocess.run(["caesar.bdd", caesar_option, reduced_nupn], stdout=subprocess.PIPE)
            caesar_bdd_time = time.time() - start_time
            assert caesar_bdd_data.returncode in (0, 5), "Unexpected error while computing the concurrency matrix of the reduced net"
            reduced_matrix, complete_matrix = matrix_from_str(caesar_bdd_data.stdout.decode('utf-8'))
            if args.sub_parsers == 'dead':
                reduced_matrix = reduced_matrix[0]
        else:
            log.info("> Read the {} of the reduced net".format(computation))
            caesar_bdd_time = 0
            with open(args.reduced_matrix) as fp:
                matrix_data = fp.read()
            reduced_matrix, complete_matrix = matrix_from_str(matrix_data)

    else:
        # Fully reducible net case
        start_time = time.time()
        reduced_matrix = ''
        complete_matrix = True
        caesar_bdd_time = 0

    # Show the reduced matrix / vector if enabled
    if args.show_reduced_result:
        print("# Reduced {}".format(computation))
        show_matrix(reduced_matrix, reduced_net, args.no_rle, args.place_names)

    # Draw graph if option enabled
    if args.draw_graph:
        tfg.draw_graph()

    # Change of Basis
    log.info("> Change of dimension")
    if args.sub_parsers == 'dead':
        vector = tfg.dead_places_vector(reduced_matrix, complete_matrix)
        show_matrix(vector, initial_net, args.no_rle, args.place_names)
    else:
        matrix = tfg.concurrency_matrix(reduced_matrix, complete_matrix)
        show_matrix(matrix, initial_net, args.no_rle, args.place_names)

    # Show computation time
    if args.time:
        computation_time = time.time() - start_time
        change_basis_time = computation_time - caesar_bdd_time
        print("# Computation time: {} (Caesar.bdd: {} + Change of Dimension: {})".format(computation_time, caesar_bdd_time, change_basis_time))

    if f_pnml is not None:
        f_pnml.close()

    if f_net is not None:
        f_net.close()

    if not (args.save_reduced_net or args.reduced_net):
        f_reduced_net.close()

    f_reduced_pnml.close()


def reach(args):
    """ Marking reachability decision procedure.
    """
    # Quit if no marking specified
    if args.marking is None:
        print("No marking specified.")
        return

    # Start time
    start_time = time.time()

    # Set input file
    infile = args.infile

    # Read initial Petri net
    log.info("> Read the input net")
    initial_net = PetriNet(infile, initial_net=True)
    infile = initial_net.filename

    # Manage reduced net
    f_reduced_net = None
    if args.reduced_net:
        reduced_net_filename = args.reduced_net
    else:
        log.info("> Reduce the input net")
        if args.save_reduced_net:
            reduced_net_filename = args.infile.replace('.pnml', '_reduced.net')
        else:
            f_reduced_net = tempfile.NamedTemporaryFile(suffix='.net')
            reduced_net_filename = f_reduced_net.name

        reduction_time = time.time()
        if not args.shrink and which("reduce") is not None:
            subprocess.run(["reduce", "-rg,redundant,compact,4ti2", "-redundant-limit", "650", "-redundant-time", "10", "-inv-limit", "1000", "-inv-time", "10", "-PNML", infile, reduced_net_filename], check=True)
        else:
            subprocess.run(["shrink", "--equations", "--clean", "--redundant", "--compact", "-i", infile, "-o", reduced_net_filename], check=True)

        if args.time:
            print("# Reduction time:", time.time() - reduction_time)

    # Read reduced net
    log.info("> Read the reduced net")
    reduced_net = PetriNet(reduced_net_filename)

    # Show reduction ratio if option enabled
    if args.show_reduction_ratio:
        print("# Reduction ratio:", (1 - reduced_net.number_places / initial_net.number_places) * 100)

    # Build the Token Flow Graph
    log.info("> Build the Token Flow Graph")
    tfg = TFG(reduced_net_filename, initial_net, reduced_net, args.show_equations)

    # Draw graph if option enabled
    if args.draw_graph:
        tfg.draw_graph()

    # Read marking
    log.info("> Read the marking")
    with open(args.marking) as fp:
        marking_str = fp.read()
    marking = marking_parser(marking_str)

    # Project marking
    log.info("> Prokect the marking")
    reduced_marking = tfg.marking_projection(marking)

    if reduced_marking is None:
        # Case: no possible projection
        print("UNREACHABLE")
        sift_time = 0
    elif not reduced_marking:
        # Case: tautological projection
        print("REACHABLE")
        sift_time = 0
    else:
        # Case: projection to check
        formula = '- (' + ' /\ '.join('{} = {}'.format(place, tokens) for place, tokens in reduced_marking.items()) + ')'
        
        if args.show_projected_marking:
            print("# Projected marking:", formula)

        log.info("> Query to sift")
        with tempfile.NamedTemporaryFile(mode="w+t") as tmp:
            tmp.writelines(formula)
            tmp.seek(0)
            sift_time = time.time()
            sift = subprocess.run(["sift", reduced_net_filename, "-ff", tmp.name], stdout=subprocess.PIPE, check=True)
        sift_time = time.time() - sift_time
        if "some state violates condition -f:" == sift.stdout.decode('utf-8').splitlines()[0]:
            print("REACHABLE")
        else:
            print("UNREACHABLE")

    # Show computation time
    if args.time:
        print("# Computation time: {} (sift: {})".format(time.time() - start_time, sift_time))

    # Close temporary files
    if not (args.save_reduced_net or args.reduced_net):
        f_reduced_net.close()


def main():
    """ Main Function.
    """
    # Arguments parser
    parser = argparse.ArgumentParser(description='Koncurrent places Grinder')

    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s 2.0.0',
                        help='show the version number and exit')

    sub_parsers = parser.add_subparsers(help='Mode', dest='sub_parsers')

    parent_parser = argparse.ArgumentParser(add_help=False)

    parent_parser.add_argument('-v', '--verbose',
                               action='store_true',
                               help='increase output verbosity')

    parent_parser.add_argument('-sk', '--shrink',
                               action='store_true',
                               help='use the Shrink reduction tool')

    group_reductions = parent_parser.add_mutually_exclusive_group()

    group_reductions.add_argument('-sr', '--save-reduced-net',
                                  action='store_true',
                                  help='save the reduced net')

    group_reductions.add_argument('-rn', '--reduced-net',
                                  action='store',
                                  dest='reduced_net',
                                  type=str,
                                  help='specify reduced Petri net (.net format)')

    parent_parser.add_argument('-t', '--time',
                               action='store_true',
                               help='show the computation time')

    parent_parser.add_argument('-srr', '--show-reduction-ratio',
                               action='store_true',
                               help='show the reduction ratio')

    parent_parser.add_argument('-se', '--show-equations',
                               action='store_true',
                               help='show the reduction equations')

    parent_parser.add_argument('-dg', '--draw-graph',
                               action='store_true',
                               help='draw the Token Flow Graph')

    conc_dead_parser = argparse.ArgumentParser(add_help=False)

    conc_dead_parser.add_argument('infile',
                                  metavar='filename',
                                  type=str,
                                  help='input Petri net (.pnml or .nupn format)')

    conc_dead_parser.add_argument('-nu', '--no-units',
                                  action='store_true',
                                  help='disable units propagation')

    conc_dead_parser.add_argument('-nr', '--no-rle',
                                  action='store_true',
                                  help='disable run-length encoding (RLE)')

    conc_dead_parser.add_argument('-pl', '--place-names',
                                  action='store_true',
                                  help='show place names')

    conc_dead_parser.add_argument('-sn', '--show-nupns',
                                  action='store_true',
                                  help='show the NUPNs')

    conc_dead_parser.add_argument('--bdd-timeout',
                                  action='store',
                                  dest='bdd_timeout',
                                  type=int,
                                  help='set the time limit for marking graph exploration (caesar.bdd)')

    conc_dead_parser.add_argument('--bdd-iterations',
                                  action='store',
                                  dest='bdd_iterations',
                                  type=int,
                                  help='set the limit for number of iterations for marking graph exploration (caesar.bdd)')

    parser_conc = sub_parsers.add_parser('conc', parents=[parent_parser, conc_dead_parser], help='Concurrent places computation')

    parser_conc.add_argument('-rm', '--reduced-matrix',
                              action='store',
                              dest='reduced_result',
                              type=str,
                              help='specify reduced concurrency matrix (or dead places vector) file')

    parser_conc.add_argument('-srm', '--show-reduced-matrix',
                              action='store_true',
                              dest='show_reduced_result',
                              help='show the reduced matrix')

    parser_dead = sub_parsers.add_parser('dead', parents=[parent_parser, conc_dead_parser], help='Dead places computation')

    parser_dead.add_argument('-rm', '--reduced-vector',
                             action='store',
                             dest='reduced_result',
                             type=str,
                             help='specify reduced dead places vector file')

    parser_dead.add_argument('-srv', '--show-reduced-vector',
                             action='store_true',
                             dest='show_reduced_result',
                             help='show the reduced vector')

    parser_reach = sub_parsers.add_parser('reach', parents=[parent_parser], help='Marking reachability decision')

    parser_reach.add_argument('infile',
                              metavar='filename',
                              type=str,
                              help='input Petri net (.pnml or .net format)')

    parser_reach.add_argument('-m', '--marking',
                              action='store',
                              dest='marking',
                              type=str,
                              help='marking')

    parser_reach.add_argument('-sf', '--show-projected-marking',
                              action='store_true',
                              help='show the projected marking')

    args = parser.parse_args()

    # Call corresponding function
    sub_parsers = args.sub_parsers
    if sub_parsers is None:
        parser.print_usage()
    else:
        globals()[sub_parsers](args)


if __name__ == '__main__':
    sys.setrecursionlimit(10000)
    main()
    exit(0)
