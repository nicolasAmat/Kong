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

from graphviz import Graph


class TFG:
    """
    Token Flow Graph method.
    """

    def __init__(self, filename, initial_net, reduced_net, complete_matrix, matrix_reduced=[], show_equations=False, draw_graph=False):
        """ Initializer.
        """
        # Petri nets
        self.initial_net = initial_net
        self.reduced_net = reduced_net

        # Nodes initialization
        self.nodes = {}
        self.init_nodes()
        self.marked_root = self.get_node('1')
        self.dead_root = self.get_node('0')

        # Parse the system of equations and build the Token Flow Graph
        self.parse_system(filename, show_equations)
        if draw_graph:
            self.draw_TFG()

        # Matrices initialization
        self.complete_matrix = complete_matrix
        self.matrix_reduced = matrix_reduced
        if self.complete_matrix:
            relation = '0'
        else:
            relation = '.'
        self.matrix_initial = [[relation for _ in range(i + 1)] for i in range(self.initial_net.number_places)]

    def draw_TFG(self):
        """ Draw the Token Flow Graph.
        """
        tfg = Graph('TFG')

        # Draw nodes
        tfg.attr('node', shape='circle', fixedsize='True')
        for node in self.nodes.values():
            tfg.node(node.id)

        # Draw redundant arcs
        tfg.attr('edge', arrowhead='dotnormal', arrowtail='none')
        for node in self.nodes.values():
            for redundant in node.redundant:
                tfg.edge(node.id, redundant.id, dir='both')

        # Draw agglomerated arcs
        tfg.attr('edge', arrowhead='normal', arrowtail='odot')
        for node in self.nodes.values():
            for agglomerated in node.agglomerated:
                tfg.edge(node.id, agglomerated.id, dir='both')

        tfg.view()

    def init_nodes(self):
        """ Create a node for each place from the initial net.
        """
        for place in self.initial_net.places:
            self.nodes[place] = Node(place)

    def get_node(self, id_node):
        """ Return the node that corresponds to the id if it exists,
            otherwise create a new one and return it.
        """
        if id_node in self.nodes:
            return self.nodes[id_node]
        else:
            node = Node(id_node, additional=True)
            self.nodes[id_node] = node
            return node

    def parse_system(self, filename, show_equations):
        """ System of equations parser.
            Input format: .net (output of the `reduce` tool)
        """
        try:
            with open(filename, 'r') as fp:
                content = re.search(r'# generated equations\n(.*)?\n\n', fp.read(), re.DOTALL)
                if content:
                    if show_equations:
                        print("# System of equations")
                    for line in re.split('\n+', content.group())[1:-1]:
                        if show_equations:
                            print(line)
                        self.parse_equation(re.split(r'\s+', line.replace(' |- ', ' ').replace('# ', '').replace(' <= ', ' ').replace(' = ', ' ').replace(' + ', ' ').replace('{', '').replace('}', '')))
            fp.close()

        except FileNotFoundError as e:
            exit(e)

    def parse_equation(self, equation):
        """ Equation parser.
            Input format: .net (output of the `reduced` tool)
        """
        # Split equation
        kind = equation.pop(0)
        nodes = [self.get_node(id_node) for id_node in equation]

        # Redundance (Constant or Duplication or Shortcut)
        if kind == 'R':
            removed_place = nodes.pop(0)
            for node in nodes:
                node.redundant.append(removed_place)
            return

        # Agglomeration
        if kind == 'A':
            new_place = nodes.pop(0)
            new_place.agglomerated += nodes
            return

        raise ValueError("Invalid reduction equation")

    def change_of_basis(self):
        """ Change of Basis method.
        """
        # Propagate marked root
        self.token_propagation(self.marked_root, '1', memoize=True)
        # Partial relation case
        if not self.complete_matrix:
            # Propagate dead root
            self.token_propagation(self.dead_root, '0', memoize=True)
            # Product with marked root
            self.product(self.marked_root.children, self.dead_root.children, '0')

        # Propagate roots values (from the reduced net)
        for i in range(self.reduced_net.number_places):
            node = self.get_node(self.reduced_net.places[i])
            value = self.matrix_reduced[i][i]

            # Reachable root
            if value == '1':
                self.token_propagation(node, value, memoize=True)
                # Product with marked root
                self.product(self.marked_root.children, node.children, value)

            # Partial relation case
            if not self.complete_matrix:
                # Non necessary reachable root propagation
                if value != '1':
                    self.token_propagation(node, value, memoize=True)
                # Product with dead root
                self.product(self.dead_root.children, node.children, '0')
                # Product with marked root
                if value == '0':
                    self.product(self.marked_root.children, node.children, '0')

        # Propagate the concurrency relation from the reduced matrix
        for i, line in enumerate(self.matrix_reduced):
            for j, concurrency in enumerate(line[:-1]):
                # If two root are concurrent then each pair of children are concurrent
                if concurrency == '1':
                    node1, node2 = self.get_node(self.reduced_net.places[i]), self.get_node(self.reduced_net.places[j])
                    self.product(node1.children, node2.children, '1')
                # Partial relation case
                # (If two roots are independent then each pair of children are independent too,
                # except for the intersection that is managed by the product method.)
                if not self.complete_matrix and concurrency == '0':
                    node1, node2 = self.get_node(self.reduced_net.places[i]), self.get_node(self.reduced_net.places[j])
                    self.product(node1.children, node2.children, '0')

        return self.matrix_initial

    def token_propagation(self, node, value, memoize=False):
        """ Token propagation:
            - propagate reachable/dead places,
            - learn new concurrent/independent places,
            - memoize children.
        """
        # Initialization
        children = []

        # If the node is a place from the initial net:
        # - add the value (not '.') in the concurrency matrix (reachable / dead),
        # - add to the children list.
        if not node.additional:
            if value != '.':
                order = self.initial_net.order[node.id]
                if self.matrix_initial[order][order] != '1':
                    self.matrix_initial[order][order] = value
            children.append(node)

        # Token propagation over the agglomerated nodes
        for agglomerated in node.agglomerated:
            new_children = self.token_propagation(agglomerated, value)
            # Partial relation case
            if not self.complete_matrix:
                # Learn new independent places
                self.product(new_children, children, '0')
            children += new_children

        # Token propagation over the redundant nodes
        for redundant in node.redundant:
            new_children = self.token_propagation(redundant, value)
            # Learn new concurrent/independent places
            if value != '.':
                self.product(new_children, children, value)
            children += new_children

        # Children memoization
        if memoize:
            node.children = children

        # Return children
        return children

    def product(self, places1, places2, value):
        """ Set the cartesian product between two lists of places
            to a value in the initial matrix. 
        """
        for place1, place2 in itertools.product(places1, places2):
            place1 = self.initial_net.order[place1.id]
            place2 = self.initial_net.order[place2.id]
            # DAGs intersection management (cf. change_of_basis method)
            if value == '1' or self.matrix_initial[max(place1, place2)][min(place1, place2)] == '.':
                self.matrix_initial[max(place1, place2)][min(place1, place2)] = value


class Node:
    """
    Node: place or additional variable.

    A node is defined by:
    - an identifier,
    - a Boolean indicating if the node is an additional variable (not in the initial net),
    - a list of redundant nodes,
    - a list of agglomerated nodes,
    - a list of children in the TFG (optional).
    """

    def __init__(self, id, additional=False):
        """ Initializer.
        """
        self.id = id
        self.additional = additional

        # Arcs
        self.redundant = []
        self.agglomerated = []

        # Descendants in the TFG that are not additional
        self.children = []
