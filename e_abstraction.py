#!/usr/bin/env python3

"""
E-Abstraction Module

Equations provided by the `reduce` tool.
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

from pt import PetriNet

import re
import sys


class System:
    """
    Equation system defined by:
    - a set of places from the initial Petri Net,
    - a set of places from the reduced Petri Net,
    - a set of additional variables,
    - a set of (in)equations.
    """

    def __init__(self, filename, places=[], places_reduced=[]):
        """ Initializer.
        """
        self.places = places
        self.places_reduced = places_reduced

        self.equations = []

        self.parser(filename)

    def __str__(self):
        """ Equations to `reduce` tool format.
        """
        return '\n'.join(map(str, self.equations))

    def parser(self, filename):
        """ System of reduction equations parser.
            Input format: .net (output of the `reduce` tool)
        """
        try:
            with open(filename, 'r') as fp:
                content = re.search(r'# generated equations\n(.*)?\n\n', fp.read(), re.DOTALL)
                if content:
                    lines = re.split('\n+', content.group())[1:-1]
                    equations = [re.split(r'\s+', line.partition(' |- ')[2]) for line in lines]
                    self.equations = [Equation(eq, self) for eq in equations]
            fp.close()
        except FileNotFoundError as e:
            exit(e)


class Equation:
    """
    Equation defined by:
    - Left member,
    - Right member,
    - Operator.
    """

    def __init__(self, eq, system):
        """ Initializer.
        """
        self.left = None
        self.right = []
        self.operator = ""

        self.parse_equation(eq, system)

    def __str__(self):
        """ Equation to 'reduce' format.
        """
        return self.left + ' = ' + ' + '.join(map(str, self.right))

    def parse_equation(self, eq, system):
        """ Equation parser.
            Input format: .net (output of the `reduced` tool)
        """
        for index, element in enumerate(eq):
            if element != '+':
                if index == 1:
                    #  element in ['=', '<=', '>=', '<', '>']
                    self.operator = element
                else:
                    element = element.replace('{', '').replace('}', '')
                    if index == 0:
                        self.left = element
                    else:
                        self.right.append(element)


class Relation:
    """
    Graph relation between a net and its reduced net.
    
    A relation is composed of:
    - Agglomerations of Variables,
    - Constant Variables,
    - Equalities between Variables.

    Used for the Concurrent Places Problem.
    See: `concurrent_places.py`
    """

    def __init__(self, system):
        self.system = system

        self.variables = {}

        self.agglomerations = []
        self.constant_vars = []
        self.equal_vars = []

        self.construct()
        self.propagate()

    def __str__(self):
        """ Relation to String:
            - Agglomerations,
            - Constant Variables,
            - Equal Variables.
        """
        text = "> Agglomerations\n"
        text += '\n'.join(map(str, self.agglomerations)) + '\n'

        text += "> Constant Variables\n"
        for pl in self.constant_vars:
            text += pl.id + ' = ' + str(pl.value) + '\n'

        text += "> Equal Variables\n"
        for eq in self.equal_vars:
            text += eq[0].id + ' = ' + eq[1].id + '\n'

        return text

    def construct(self):
        """ Parse the equations and construct the relation.
        """
        for eq in self.system.equations:

            left = self.get_variable(eq.left)

            if len(eq.right) == 1:

                if eq.right[0].isnumeric():
                    # case p = k or a = k
                    left.value = int(eq.right[0])
                    self.constant_vars.append(left)

                else:
                    # case p = q
                    right = self.get_variable(eq.right[0])
                    left.equals.append(right)
                    right.equals.append(left)
                    self.equal_vars.append([left, right])

            else:
                # case a = p + a' or a = p + q or p = q + r
                right_0, right_1 = self.get_variable(eq.right[0]), self.get_variable(eq.right[1])
                left.children.append(right_0)
                left.children.append(right_1)

                if not left.additional:
                    right_0.parent = left
                    right_1.parent = left

                self.agglomerations.append(left)

    def propagate(self):
        """ Propagate places to the head of each agglomeration.
            Propagate value of each agglomeration.
        """
        for var in self.variables.values():
            var.propagate(var.value)

    def get_variable(self, id_var):
        """ Create the corresponding Variable
            if it is not already created,
            otherwise return the corresponding Variable.
        """
        if id_var in self.variables:
            return self.variables[id_var]
        else:
            new_var = Variable(id_var, id_var not in self.system.places)
            self.variables[id_var] = new_var
            return new_var

    def trivial_c_stables(self):
        """ Return a set of c-stables obtained trivially
            from the reduction equations.
        """
        c_stables = []

        for var in self.agglomerations:
            # a_n = k > 1
            # a_n = p_n + a_n-1
            # ...
            # a_1 = p_1 + p_0
            if var.value > 1:
                c_stable = []
                for pl in var.propagated_places:
                    c_stable.append(pl.id)
                    if pl.parent:
                        c_stable.append(pl.parent.id)
                c_stables.append(c_stable)

            # p = q + r
            if not var.additional:
                self.add_c_stable(c_stables, var, var.children[0])
                self.add_c_stable(c_stables, var, var.children[1])

        # constant places and agglomerations (assumption: No dead place)
        for var in self.constant_vars:
            for pl1 in var.propagated_places:
                for pl2 in self.system.places:
                    if pl2 not in var.propagated_places:
                        self.add_c_stable(c_stables, pl1, self.get_variable(pl2))

        # equals variables
        for (var1, var2) in self.equal_vars:
            if not (var1.additional or var2.additional):
                self.add_c_stable(c_stables, var1, var2)

        return c_stables

    def c_stable_matrix(self, var1_id, var2_id):
        """ Given two concurrent places from the reduced net
            return associated c-stables in the initial net.
        """
        var1 = self.get_variable(var1_id)
        var2 = self.get_variable(var2_id)

        c_stables = []

        for pl1 in var1.propagated_places:
            for pl2 in var2.propagated_places:
                self.add_c_stable(c_stables, pl1, pl2)

        return c_stables

    def add_c_stable(self, c_stables, pl1, pl2):
        """
        """
        c_stables.append([pl1.id, pl2.id])

        if pl1.parent:
            c_stables.append([pl1.parent.id, pl2.id])

        if pl2.parent:
            c_stables.append([pl1.id, pl2.parent.id])

        if pl1.parent and pl2.parent:
            c_stables.append([pl1.parent.id, pl2.parent.id])


class Variable:
    """
    Place or additional variable.
    Used by the Concurrency Matrix Constructor.
    A variable defined by:
    - an ID,
    - a value,
    - a list of equals variables,
    - a list of children,
    - after propagation, a set of places associated.

    Used for the Concurrent Places Problem.
    See: `concurrent_places.py`
    """

    def __init__(self, id, additional):
        self.id = id
        self.additional = additional
        
        self.children = []
        self.parent = None

        self.value = -1
        self.equals = []

        self.propagated_places = set()

        if not self.additional:
            self.propagated_places.add(self)

    def __str__(self):
        text = self.id + ':'
        for var in self.propagated_places:
            text += ' ' + var.id
        return text

    def propagate(self, value):
        """ Recursive propagation for agglomerations.
        """
        # Update value
        if self.value < value:
            self.value = value

        # For each child, propagate it and add the places (recursively)
        for child in self.children:
            if not child.propagated_places:
                child.propagate(value)
            self.propagated_places = self.propagated_places.union(child.propagated_places)

        # For each equal var, propagate it and add the places (recursively)
        for equal in self.equals:
            if not equal.propagated_places:
                equal.propagate(value)
            self.propagated_places = self.propagated_places.union(equal.propagated_places)


if __name__ == "__main__":

    if len(sys.argv) < 4:
        exit("File missing: ./e_abstraction <path_to_initial_net> <path_to_reduced_net> <path_to_equations>")

    initial_net = PetriNet(sys.argv[1])
    reduced_net = PetriNet(sys.argv[2])

    system = System(sys.argv[3], initial_net.places, reduced_net.places)

    relation = Relation(system)

    print("System of Equations")
    print("---------")
    print(system)

    print("Relations")
    print("---------")
    print(relation)
