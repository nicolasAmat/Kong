#!/usr/bin/env python3

"""
Concurrency Matrix Module

Input file format: caesar.bdd format (half matrix with run-lenght encoding)

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

from e_abstraction import Relation

import itertools

class ConcurrencyMatrix:
    """ Concurrency Matrix Computer.
        (based on the 'Change of Basis' method)
    """

    def __init__(self, initial_net, reduced_net, system, matrix_reduced):
        """ Initializer.
        """
        self.intial_net = initial_net
        self.reduced_net = reduced_net

        self.matrix_reduced = []
        self.fill_matrix_from_str(matrix_reduced)
        
        self.matrix_initial = [[0 for j in range(i + 1)] for i in range(self.intial_net.number_places)]
        for i in range(self.intial_net.number_places):
            self.matrix_initial[i][i] = 1

        self.relation = Relation(system)
        self.change_basis()

        self.display_matrix()

    def fill_matrix_from_str(self, matrix):
        """ Fill matrix from caesar.bdd output.
            (with run-length encoding)
        """
        matrix = matrix.replace('(', '').replace(')', '').split('\n')
        
        for line in matrix:
            if len(line) == 0:
                break

            new_line = []
            past_value = -1

            for value in line:
                value = int(value)
                if value > 1:
                    new_line.extend([past_value for _ in range(value - 1)])
                else:
                    new_line.append(value)
                    past_value = value

            self.matrix_reduced.append(new_line)
                
    def fill_matrix(self, c):
        """ Fill a c-stable c in the concurrency matrix.
        """
        for pl1, pl2 in itertools.combinations(c, 2):
            pl1_order, pl2_order = self.intial_net.order_places[pl1], self.intial_net.order_places[pl2]
            if pl1_order > pl2_order:
                self.matrix_initial[pl1_order][pl2_order] = 1
            else:
                self.matrix_initial[pl2_order][pl1_order] = 1

    def change_basis(self):
        """ Change of basis.
        """
        c_stables = self.relation.trivial_c_stables()
        for c_stable in c_stables:
            self.fill_matrix(c_stable)

        for i, line in enumerate(self.matrix_reduced):
            for j, concurrency in enumerate(line):
                if i != j and concurrency == 1:
                    var1 = self.reduced_net.places[i]
                    var2 = self.reduced_net.places[j]
                    if var1 not in self.intial_net.places or var2 not in self.intial_net.places:
                        c_stables = self.relation.c_stable_matrix(var1, var2)
                        for c_stable in c_stables:
                            self.fill_matrix(c_stable)
                    else:
                        self.fill_matrix([var1, var2])

    def display_matrix(self):
            """ Display concurrency matrix.
                (with run-length encoding)
            """
            max_len = max([len(pl) for pl in self.intial_net.places])

            for pl, line in zip(self.intial_net.places, self.matrix_initial):
                text = pl + " " * (max_len - len(pl) + 2)
                for i in range(len(line)):
                    elem = line[i]
                    if i == 0:
                        previous = elem
                        counter = 0
                    if i == len(line) - 1:
                        if previous != elem:
                            text += self.compression_rle(previous, counter)
                            text += str(elem)
                        else:
                            text += self.compression_rle(previous, counter + 1)
                    else:
                        if elem != previous:
                            text += self.compression_rle(previous, counter)
                            previous = elem
                            counter = 1
                        else:
                            counter += 1
                print(text)

    def compression_rle(self, elem, counter):
        """ Run-length encoding helper.
        """
        if counter < 4:
            return str(elem) * counter
        else:
            return "{}({})".format(elem, counter)