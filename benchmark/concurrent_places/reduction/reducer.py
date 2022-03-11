#!/usr/bin/env python3

"""
Reducion Benchmark Script

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
__version__ = "2.0.0"

import argparse
import subprocess
import sys
import tempfile
import time

sys.path.append('../../kong/')
from pt import PetriNet


def main():
    """ Main Function.
    """
    # Arguments parser
    parser = argparse.ArgumentParser(description='Reducion Benchmark Script')

    parser.add_argument('net',
                        metavar='filename',
                        type=str,
                        help='input Petri net (.pnml or .nupn format)')

    results = parser.parse_args()

    # Read initial Petri net
    initial_net = PetriNet(results.net, initial_net=True)
    infile = initial_net.filename

    # TFG reductions (as used with Kong)
    f_reduced_net = tempfile.NamedTemporaryFile(suffix='.net')
    reduced_net_filename = f_reduced_net.name
    reduction_time = time.time()
    subprocess.run(["reduce", "-rg,redundant,compact,4ti2", "-redundant-limit", "650", "-redundant-time", "10", "-inv-limit", "1000", "-inv-time", "10", "-PNML", infile, reduced_net_filename], check=True)
    print("# TFG time:", time.time() - reduction_time)
    f_reduced_pnml = tempfile.NamedTemporaryFile(suffix='.pnml')
    subprocess.run(["ndrio", reduced_net_filename, f_reduced_pnml.name], check=True)
    reduced_net = PetriNet(f_reduced_pnml.name)
    print("# TFG ratio:", (1 - reduced_net.number_places / initial_net.number_places) * 100)

    # Reduce reductions (as used with the SMPT model-checker)
    f_reduced_net = tempfile.NamedTemporaryFile(suffix='.net')
    reduced_net_filename = f_reduced_net.name
    reduction_time = time.time()
    subprocess.run(["reduce", "-rg,redundant,compact+,mg,4ti2", "-redundant-limit", "650", "-redundant-time", "10", "-inv-limit", "1000", "-inv-time", "10", "-PNML", infile, reduced_net_filename], check=True)
    print("# Reduce time:", time.time() - reduction_time)
    f_reduced_pnml = tempfile.NamedTemporaryFile(suffix='.pnml')
    subprocess.run(["ndrio", reduced_net_filename, f_reduced_pnml.name], check=True)
    reduced_net = PetriNet(f_reduced_pnml.name)
    print("# Reduce ratio:", (1 - reduced_net.number_places / initial_net.number_places) * 100)


if __name__ == '__main__':
    sys.setrecursionlimit(10000)
    main()
    exit(0)
