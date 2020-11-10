#!/usr/bin/env python3

"""
Token Flow Graph Method

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

import itertools
import re

class TFG:
    """
    Token Flow Graph method.
    """

    def __init__(self, filename, places_initial, places_reduced, matrix_reduced=[]):
        """ Initializer.
        """
        self.places_initial = places_initial
        self.places_reduced = places_reduced

        self.variables = {}
        self.constants = set()
        self.init_variables()

        self.parse_system(filename)

        self.matrix_reduced = matrix_reduced
        self.matrix = [[0 for j in range(i + 1)] for i in range(len(self.places_initial))]

        self.leafs = {}

    def init_variables(self):
        """ Create a Variable for each place from the initial net.
        """
        for place in self.places_initial:
            self.variables[place] = Variable(place)

    def get_variable(self, id_var):
        """ Return the corresponding Variable,
            or create a new Variable if it does not exist.
        """
        if id_var in self.variables:
            return self.variables[id_var]
        else:
            var = Variable(id_var, additional=True)
            self.variables[id_var] = var
            return var

    def parse_system(self, filename):
        """ System of reduction equations parser.

            Input format: .net (output of the `reduce` tool)
        """
        try:
            with open(filename, 'r') as fp:
                content = re.search(r'# generated equations\n(.*)?\n\n', fp.read(), re.DOTALL)
                if content:
                    for line in re.split('\n+', content.group())[1:-1]:
                        equation = re.split(r'\s+', line.replace(' |- ', ' ').replace('# ', '').replace('<=', '').replace('=', '').replace('+', '').replace('{', '').replace('}', ''))
                        self.parse_equation(equation)

            fp.close()
        except FileNotFoundError as e:
            exit(e)

    def parse_equation(self, equation):
        """ Equation parser.
        
            Input format: .net (output of the `reduced` tool)
        """
        kind = equation.pop(0)

        if equation[-1].isnumeric():
            self.constants.add(self.get_variable(equation[0]))
            return

        variables = [self.get_variable(var) for var in equation]

        if kind == 'R':
            removed_place = variables.pop(0)
            for var in variables:
                var.redundant.append(removed_place)
            return

        if kind == 'A':
            new_place = variables.pop(0)
            for var in variables:
                new_place.agglomerated.append(var)
            return

        raise ValueError("Invalid reduction equation")

    def change_of_basis(self):
        """ Change of Basis method.
        """
        for var in self.constants:
            self.propagation(var, get_leafs=True, memoize=True)

        for i in range(len(self.matrix_reduced)):
            if self.matrix_reduced[i][i]:
                self.propagation(self.get_variable(self.places_reduced[i]), get_leafs=True, memoize=True)
 
        for i, line in enumerate(self.matrix_reduced):
            for j, concurrency in enumerate(line[:-1]):
                if concurrency:
                    var1 = self.get_variable(self.places_reduced[i])
                    var2 = self.get_variable(self.places_reduced[j])
                    self.product(self.leafs[var1], self.leafs[var2])

        non_dead = {var for var in self.variables.values() if not var.additional and var.reachable}

        for var in self.constants:
            self.product(self.leafs[var], non_dead - set(self.leafs[var]))

        return self.get_matrix()

    def propagation(self, var, get_leafs=False, memoize=False):
        """ Token propagation.
        """
        # Variable is reachable
        var.reachable = True

        leafs, concurrency, concurrency_red = [], False, False

        # Product of the leafs if two redundances or one redundance + one agglomeration
        if len(var.redundant) > 1 or (var.agglomerated and var.redundant):
            get_leafs, concurrency = True, True

        if not var.additional and var.redundant:
            get_leafs, concurrency_red = True, True

        # Propagate children
        if concurrency:
            agg_leafs = []
            for child in var.agglomerated:
                agg_leafs += self.propagation(child, get_leafs)
                leafs += agg_leafs
        
            red_leafs = []
            for child in var.redundant:
                red_leafs.append(self.propagation(child, get_leafs))

            if len(red_leafs) == 2:
                self.product(red_leafs[0], red_leafs[1])
        
            for red in red_leafs:
                self.product(agg_leafs, red)
                leafs += red
        
        if concurrency_red:
            red_leafs = []
            for child in var.redundant:
                red_leafs.append(self.propagation(child, get_leafs))

            for red in red_leafs:
                self.product([var], red)
                leafs += red

        if not concurrency and not concurrency_red:
            for child in var.agglomerated + var.redundant:
                leafs += self.propagation(child, get_leafs)

        # A leaf is a place from the initial net
        if not var.additional:
            leafs.append(var)

        if memoize:
            self.leafs[var] = leafs

        if get_leafs:
            return leafs
        else:
            return []

    def product(self, places_1, places_2):
        """
        """
        for place_1, place_2 in itertools.product(places_1, places_2):
            # TODO: matrix directly
            place_1.concurrent.add(place_2)
            place_2.concurrent.add(place_1)

    def get_matrix(self):
        """ Get concurrency matrix from the initial net (after a change of basis).
        """
        matrix = [[0 for j in range(i + 1)] for i in range(len(self.places_initial))]

        for i, pl1 in enumerate(self.places_initial):
            for j, pl2 in enumerate(self.places_initial[:i+1]):
                var1, var2 = self.get_variable(pl1), self.get_variable(pl2)
                if (i == j and var1.reachable) or var2 in var1.concurrent:
                    matrix[i][j] = 1

        return matrix


class Variable:
    """
    Place or additional variable.

    A variable defined by:
    - an identifier,
    """

    def __init__(self, id, additional=False):
        """ Initializer.
        """
        self.id = id
        self.additional = additional

        self.redundant = []
        self.agglomerated = []

        self.concurrent = set()

        self.reachable = False
