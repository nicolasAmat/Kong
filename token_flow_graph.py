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

    def __init__(self, filename, initial_net, reduced_net, matrix_reduced=[]):
        """ Initializer.
        """
        self.initial_net = initial_net
        self.reduced_net = reduced_net

        self.variables = {}
        self.reachable = set()
        self.init_variables()

        self.constants = set()
        self.parse_system(filename)

        self.leafs = {}

        self.matrix_reduced = matrix_reduced
        self.matrix_initial = [[0 for j in range(i + 1)] for i in range(self.initial_net.number_places)]

    def init_variables(self):
        """ Create a Variable for each place from the initial net.
        """
        for place in self.initial_net.places:
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
                        self.parse_equation(re.split(r'\s+', line.replace(' |- ', ' ').replace('# ', '').replace('<=', '').replace('=', '').replace('+', '').replace('{', '').replace('}', '')))

            fp.close()
        except FileNotFoundError as e:
            exit(e)

    def parse_equation(self, equation):
        """ Equation parser.
            Input format: .net (output of the `reduced` tool)
        """
        kind = equation.pop(0)

        # Constant
        if equation[-1].isnumeric() and int(equation[-1]) != 0:
            self.constants.add(self.get_variable(equation[0]))
            return

        variables = [self.get_variable(id_var) for id_var in equation]

        # Redundant (Duplicated or Shortcut)
        if kind == 'R':
            removed_place = variables.pop(0)
            for var in variables:
                var.redundant.append(removed_place)
            return

        # Agglomeration
        if kind == 'A':
            new_place = variables.pop(0)
            new_place.agglomerated += variables
            return

        raise ValueError("Invalid reduction equation")

    def change_of_basis(self):
        """ Change of Basis method.
        """
        # Propagate constant variables
        for var in self.constants:
            self.token_propagation(var, get_leafs=True, memoize=True)

        # Propagate reachable roots
        for i in range(self.reduced_net.number_places):
            if self.matrix_reduced[i][i]:
                var = self.get_variable(self.reduced_net.places[i])
                self.token_propagation(var, get_leafs=True, memoize=True)

        # Add concurrency relations from reduced matrix
        for i, line in enumerate(self.matrix_reduced):
            for j, concurrency in enumerate(line[:-1]):
                if concurrency:
                    var1, var2 = self.get_variable(self.reduced_net.places[i]), self.get_variable(self.reduced_net.places[j])
                    self.product(self.leafs[var1], self.leafs[var2])

        # Add concurrency relations for constant variables
        for var in self.constants:
            self.product(self.leafs[var], self.reachable - set(self.leafs[var]))

        return self.matrix_initial

    def token_propagation(self, var, get_leafs=False, memoize=False):
        """ Token propagation:
            - learn concurrency relations,
            - memoize leafs.
        """
        # Initialization
        leafs = []

        # If place from the initial net, add to reachable
        if not var.additional:
            self.reachable.add(var)
            order = self.initial_net.order[var.id]
            self.matrix_initial[order][order] = 1
            # A leaf is a place from the initial net
            leafs.append(var)

        if var.redundant:
            # If redundant, learn new concurrency relations
            for agglomeration in var.agglomerated:
                leafs += self.token_propagation(agglomeration, get_leafs=True)
        
            for redundant in var.redundant:
                new_leafs = self.token_propagation(redundant, get_leafs=True)
                self.product(new_leafs, leafs)
                leafs += new_leafs

        else:
            # Otherwise, continue propagation
            for child in var.agglomerated + var.redundant:
                leafs += self.token_propagation(child, get_leafs=get_leafs)

        # Leafs memoization
        if memoize:
            self.leafs[var] = leafs

        # Return leafs
        if get_leafs:
            return leafs
        else:
            return []

    def product(self, places_1, places_2):
        """ Add the cartesian product between two sets to the concurrent relation.
        """
        for place_1, place_2 in itertools.product(places_1, places_2):
            place_1 = self.initial_net.order[place_1.id]
            place_2 = self.initial_net.order[place_2.id]
            self.matrix_initial[max(place_1, place_2)][min(place_1, place_2)] = 1


class Variable:
    """
    Place or additional variable.

    A variable is defined by:
    - an identifier,
    - a Boolean indicating if the variable is additional,
    - a list of redundant variables,
    - a list of agglomerated variables.
    """

    def __init__(self, id, additional=False):
        """ Initializer.
        """
        self.id = id
        self.additional = additional

        self.redundant = []
        self.agglomerated = []
