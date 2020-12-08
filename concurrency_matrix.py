#!/usr/bin/env python3

"""
Concurrency Matrix Module

Input file format: caesar.bdd format (half matrix with run-lenght encoding),
                   `reduced` output format (.net).

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

from token_flow_graph import TFG


class ConcurrencyMatrix:
    """ Change of basis of the concurrency matrix.
    """

    def __init__(self, initial_net, reduced_net, filename_system, matrix_reduced, place_names=False, show_equations=False, draw_graph=False, show_reduced_matrix=False):
        """ Initializer.
        """
        self.initial_net = initial_net
        self.reduced_net = reduced_net

        # Parse the reduced Petri net concurrency matrix
        self.matrix_reduced = []
        self.fill_matrix_from_str(matrix_reduced)

        # Construct the TFG
        self.method = TFG(filename_system, self.initial_net, self.reduced_net, self.matrix_reduced, show_equations, draw_graph)

        # Display the concurrency matrix of the reduced net if asked
        if show_reduced_matrix:
            print("# Reduced net concurrency matrix")
            self.display_matrix(self.reduced_net, self.matrix_reduced, place_names)

        # Change of basis
        self.matrix_initial = self.method.change_of_basis()
        # Display the concurrency matrix
        self.display_matrix(self.initial_net, self.matrix_initial, place_names)

    def fill_matrix_from_str(self, matrix):
        """ Fill matrix from caesar.bdd output.
            (with run-length encoding)
        """
        matrix = matrix.split('\n')
        
        for line in matrix:
            if len(line) == 0:
                break

            new_line = []
            past_value = -1
            parse_multiplier = False
            multiplier = ""

            for value in line:           
                if value == '(':
                    parse_multiplier = True
                elif value == ')':
                    new_line.extend([past_value for _ in range(int(multiplier) - 1)])
                    parse_multiplier = False
                    multiplier = ""
                elif parse_multiplier:
                    multiplier += value
                else:
                    new_line.append(int(value))
                    past_value = int(value)

            self.matrix_reduced.append(new_line)

    def display_matrix(self, net, matrix, place_names):
            """ Display concurrency matrix.
                (with run-length encoding)
            """
            if place_names:
                max_len = max([len(pl) for pl in net.places])

            if net == self.reduced_net:
                prefix = '# '
            else:
                prefix = ''

            for pl, line in zip(net.places, matrix):
                if place_names:
                    text = prefix + pl + ' ' * (max_len - len(pl) + 2)
                else:
                    text = prefix
                for i in range(len(line)):
                    elem = line[i]
                    if i == 0:
                        previous = elem
                        counter = 0
                    if i == len(line) - 1:
                        if previous != elem:
                            text += self.rle_compression(previous, counter)
                            text += str(elem)
                        else:
                            text += self.rle_compression(previous, counter + 1)
                    else:
                        if elem != previous:
                            text += self.rle_compression(previous, counter)
                            previous = elem
                            counter = 1
                        else:
                            counter += 1
                print(text)

    def rle_compression(self, elem, counter):
        """ Run-length encoding helper.
        """
        if counter < 4:
            return str(elem) * counter
        else:
            return "{}({})".format(elem, counter)
