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

import re
from abc import ABC, abstractmethod


class ConcurrencyMatrix:
    """ Change of basis of the concurrency matrix.
    """

    def __init__(self, initial_net, reduced_net, filename_system, matrix_reduced, place_names):
        """ Initializer.
        """
        self.initial_net = initial_net
        self.reduced_net = reduced_net

        self.matrix_reduced = []
        self.fill_matrix_from_str(matrix_reduced)

        self.system = System(filename_system, self.initial_net.places, self.reduced_net.places, self.matrix_reduced)
        self.matrix_initial = self.system.change_of_basis()

        self.display_matrix(place_names)

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

    def display_matrix(self, place_names):
            """ Display concurrency matrix.
                (with run-length encoding)
            """
            if place_names:
                max_len = max([len(pl) for pl in self.initial_net.places])

            for pl, line in zip(self.initial_net.places, self.matrix_initial):
                if place_names:
                    text = pl + ' ' * (max_len - len(pl) + 2)
                else:
                    text = ''
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


class System:
    """
    Equation system defined by:
    - a set of places from the initial Petri Net,
    - a set of places from the reduced Petri Net,
    - a set of (in)equations.
    """

    def __init__(self, filename, places_initial, places_reduced, matrix_reduced=[]):
        """ Initializer.
        """
        self.places_initial = places_initial
        self.places_reduced = places_reduced

        self.variables = {}
        self.init_variables()

        self.reachable_places = set()
        
        self.constants = []
        self.equations = []

        self.parse_system(filename)
        self.parse_matrix(matrix_reduced)

    def __str__(self):
        """ Equations to `reduce` tool format.
        """
        return '\n'.join(map(str, self.equations))

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
                    lines = re.split('\n+', content.group())[1:-1]
                    equations = [re.split(r'\s+', line.partition(' |- ')[2].replace('=', '').replace('+', '').replace('{', '').replace('}', '')) for line in lines]

                    for equation in reversed(equations): # Read with a reversed order for agglomerations
                        equation = self.parse_equation(equation)
                        
                        # Treat constant places sepearately
                        if isinstance(equation, Constant) and not equation.place.additional:
                            self.constants.append(equation)
                        else:
                            self.equations.append(equation)

            fp.close()
        except FileNotFoundError as e:
            exit(e)

    def parse_equation(self, equation):
        """ Equation parser.
        
            Input format: .net (output of the `reduced` tool)
        """
        left = self.get_variable(equation.pop(0))

        if len(equation) == 1:
            right = equation[0]
            
            if right.isnumeric():
                return Constant(left, self.reachable_places)
            else:
                right = self.get_variable(right)
                return Duplicated([left, right], self.reachable_places)
        
        else:
            children = [self.get_variable(child) for child in equation]
        
            if left.id in self.places_initial:
                return Shortcut(left, children, self.reachable_places)
            else:
                return Agglomeration(left, children, self.reachable_places)
    
    def parse_matrix(self, matrix_reduced):
        """ Parse the concurrency matrix from the reduced net.
        """
        for i, line in enumerate(matrix_reduced):
            for j, concurrency in enumerate(line):
                if concurrency:
                    var1 = self.get_variable(self.places_reduced[i])
                    var2 = self.get_variable(self.places_reduced[j])
                    if var1 != var2:
                        var1.concurrent.add(var2)
                        var2.concurrent.add(var1)
                    else:
                        self.reachable_places.add(var1)

    def get_matrix(self):
        """ Get concurrency matrix from the initial net (after a change of basis).
        """
        matrix = [[0 for j in range(i + 1)] for i in range(len(self.places_initial))]

        for i, pl1 in enumerate(self.places_initial):
            for j, pl2 in enumerate(self.places_initial[:i+1]):
                var1, var2 = self.get_variable(pl1), self.get_variable(pl2)
                if (i == j and var1 in self.reachable_places) or var2 in var1.concurrent:
                    matrix[i][j] = 1

        return matrix

    def change_of_basis(self):
        """ Change of Basis method.

            Compute the concurrency matrix of the initial net
            from the concurrency relation of the reduced net
            and the system of equation linking both nets.
        """
        self.reachable_places.union(set([constant.place for constant in self.constants]))

        new_relation = True
        
        while new_relation:
            new_relation = False
            for equation in self.equations:
                if equation.propagate():
                    new_relation = True

        for constant in self.constants:
            constant.propagate()

        return self.get_matrix()


class Equation(ABC):
    """ Reduction equation meta-class.

        - 'a', 'b' denotes additional varialbes,
        - 'p', 'q', 'r' denotes places from the initial net.
    """

    def __init__(self, reachable_places):
        """ Initializer.
        """
        self.cc = 0
        
        self.reachable_places = reachable_places
        self.reachability_propagated = False

    @abstractmethod
    def __str__(self):
        """ Equation to the `reduce` output format.
        """
        return

    @abstractmethod
    def propagate(self):
        """ Propagate the concurrency relation.
            Returns True if new relation is found.
        """
        return

    def add_concurrency_relation(self, var1, var2):
        """ Add a concurrency relation betwen two variables.
        """
        if var1 not in var2.independant and var2 not in var1.independant:
            var1.concurrent.add(var2)
            var2.concurrent.add(var1)


class Constant(Equation):
    """ Constant place.

        Cases:
        - 'a = k',
        - 'p = k'.
    """

    def __init__(self, place, reachable_places):
        """ Initializer.
        """
        Equation.__init__(self, reachable_places)
        self.place = place
        self.reachable_places.add(self.place)

    def __str__(self):
        return "R |- {} = 1".format(self.place)

    def propagate(self):
        new_cc = len(self.reachable_places)
        if new_cc > self.cc:
            for var in self.reachable_places:
                if var != self.place and var not in self.place.concurrent:
                    Equation.add_concurrency_relation(self, self.place, var)
            self.cc = new_cc
            return True
        return False

class Duplicated(Equation):
    """ Duplication of places.

        Cases:
        - 'p = q',
        - 'p = a',
        - 'a = b'.
    """

    def __init__(self, places, reachable_places):
        """ Initializer.
        """
        Equation.__init__(self, reachable_places)
        self.places = places
     
    def __str__(self):
        return "R |- {} = {}".format(self.places[0], self.places[1])

    def propagate(self):
        new_relation = False
        
        if not self.reachability_propagated:
            for i, place in enumerate(self.places):
                if self.places[i] in self.reachable_places:
                    self.reachable_places.add(self.places[(i + 1) % 2])
                    Equation.add_concurrency_relation(self, self.places[0], self.places[1])
                    self.reachability_propagated = True
                    new_relation = True
                    break

        new_cc = sum([len(place.concurrent) for place in self.places])
        if new_cc > self.cc:
            for i, place in enumerate(self.places):
                for var in place.concurrent:
                    if var != self.places[(i + 1) % 2] and var not in self.places[(i + 1) % 2].concurrent:
                        Equation.add_concurrency_relation(self, self.places[(i + 1) % 2], var)
            self.cc = new_cc
            new_relation = True

        return new_relation

class Shortcut(Equation):
    """ Shorcut between places.

        Case:
        - p = q + r.
    """

    def __init__(self, parent, children, reachable_places):
        """ Initializer.
        """
        Equation.__init__(self, reachable_places)
        self.parent = parent
        self.children = children

    def __str__(self):
        return "R |- {} = {} + {}".format(self.parent, self.children[0], self.children[1])

    def propagate(self):
        new_relation = False
        
        if not self.reachability_propagated:
            for child in self.children:
                if child in self.reachable_places:
                    self.reachable_places.add(self.parent)
                    Equation.add_concurrency_relation(self, child, self.parent)
                    new_relation = True
                    self.reachability_propagated = True

        union = self.children[0].concurrent | self.children[1].concurrent
        new_cc = len(union)
        if new_cc > self.cc:
            for var in union:
                Equation.add_concurrency_relation(self, self.parent, var)
            self.cc = new_cc
            new_relation = True

        return new_relation


class Agglomeration(Equation):
    """ Places agglomeration.

        Cases:
        - 'a = b + p',
        - 'a = p + q'.
    """

    def __init__(self, parent, children, reachable_places):
        """ Initializer.
        """
        Equation.__init__(self, reachable_places)
        self.parent = parent
        self.children = children

    def __str__(self):
        return "A |- {} = {} + {}".format(self.parent, self.children[0], self.children[1])

    def propagate(self):
        new_relation = False

        for i, child in enumerate(self.children):
            child.independant |= self.parent.independant
            if not child.additional:
                self.children[(i + 1) % 2].independant.add(child)

        if not self.reachability_propagated:
            if self.parent in self.reachable_places:
                for child in self.children:
                    self.reachable_places.add(child)
                    self.reachability_propagated = True
                    new_relation = True

        new_cc = len(self.parent.concurrent)
        if new_cc > self.cc:
            for child in self.children:
                for var in self.parent.concurrent.copy():
                    Equation.add_concurrency_relation(self, child, var)
            self.cc = new_cc
            new_relation = True

        return new_relation

class Variable:
    """
    Place or additional variable.

    A variable defined by:
    - an identifier,
    - a set of concurrent places,
    - a set of independant places.
    """

    def __init__(self, id, additional=False):
        """ Initializer.
        """
        self.id = id
        self.additional = additional

        self.concurrent = set()
        self.independant = set()
    
    def __str__(self):
        """ Variable identifier.
        """
        return self.id
