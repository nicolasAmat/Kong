#!/usr/bin/env python3

"""
Token Flow Graph Module

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

import itertools
import re
from collections import deque

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
    
        # Non-dead roots
        self.non_dead_roots = []
        self.counter_non_dead_roots = 0

        # Dead root
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
        if id_node == '1':
            self.counter_non_dead_roots += 1
            id_node = "{}#{}".format(id_node, self.counter_non_dead_roots)
            node = Node(id_node, additional=True)
            self.nodes[id_node] = node
            self.non_dead_roots.append(node)
            return node

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
            child = nodes.pop(0)
            for parent in nodes:
                parent.redundant.append(child)
                child.parents.append(parent)
            return

        # Agglomeration
        if kind == 'A':
            parent = nodes.pop(0)
            for child in nodes:
                parent.agglomerated.append(child)
                child.parents.append(parent)
            return

        # MG (TODO: missing the full implementation for using the `mg` option in the Reduce tool)
        if kind == 'I':
            constant = nodes.pop()
            constant.agglomerated += nodes
            return

        raise ValueError("Invalid reduction equation")

    def change_of_basis(self):
        """ Change of Basis method.
        """
        # Propagate non-dead roots
        for non_dead_root in self.non_dead_roots:
            self.token_propagation(non_dead_root, '1', memoize=True)
        
        # Case: partial relation
        if not self.complete_matrix:
            # Propagate dead root
            self.token_propagation(self.dead_root, '0', memoize=True)

        # Propagate roots values (from the reduced net)
        for i in range(self.reduced_net.number_places):

            # Get corresponding root and matrix value
            root = self.get_node(self.reduced_net.places[i])
            value = self.matrix_reduced[i][i]

            # Reachable root
            if value == '1':
                self.token_propagation(root, value, memoize=True)
                # Product with non-dead roots
                for non_dead_root in self.non_dead_roots:
                    self.product(non_dead_root.successors, root.successors, value)

            # Case: partial relation and root not already propagated
            if not self.complete_matrix and value != '1':
                self.token_propagation(root, value, memoize=True)
    
        # Product with non-dead roots
        for non_dead_root_1, non_dead_root_2 in itertools.combinations(self.non_dead_roots, 2):
            self.product(non_dead_root_1.successors, non_dead_root_2.successors, '1')

        # Propagate the concurrency relation from the reduced matrix
        for i, line in enumerate(self.matrix_reduced):
            
            # Skip dead roots
            if line[i] == '0':
                continue
            
            # Only iterate over the lower triangle (symmetric relation)
            for j, concurrency in enumerate(line[:-1]):

                # The product of the concurrent roots' successors is included in the concurrency relation
                if concurrency == '1':
                    root_1, root_2 = self.get_node(self.reduced_net.places[i]), self.get_node(self.reduced_net.places[j])
                    self.product(root_1.successors, root_2.successors, '1')

                # Case: partial relation
                if not self.complete_matrix and concurrency == '0':
                    # Set roots as independent
                    root_1, root_2 = self.get_node(self.reduced_net.places[i]), self.get_node(self.reduced_net.places[j])
                    root_1.independent.add(root_2)
                    root_2.independent.add(root_1)

        # Case: partial relation
        if not self.complete_matrix:

            # Queue initialization
            queue = deque()
            for place_id in self.reduced_net.places:
                queue.append(self.get_node(place_id))

            while queue:
                # Get first node in the queue
                node = queue.popleft()

                # Iterate over the intersection of the independent places from the parents
                if node.parents:
                    for independent_node in set.intersection(*[parent.independent for parent in node.parents]): 
                        # Add the independency relation in nodes
                        node.independent.add(independent_node)
                        independent_node.independent.add(node)

                # Add the independency relation in the matrix for places from the initial net
                if not node.additional:
                    self.product([node], [independent_node for independent_node in node.independent if not independent_node.additional], '0' )

                # Add children to the queue
                for child in node.agglomerated + node.redundant:
                    queue.append(child)

        # Case: partial relation
        # Dead places are independent to all others places
        dead_columns = []
        for i, row in enumerate(self.matrix_initial):
            # If the place is dead set the row to `0` 
            if row[i] == '0':
                for j in range(len(row)):
                    row[j] = '0'
                # Add the place to the dead columns
                dead_columns.append(i)
            else:
                # If the place is not dead, set the dead columns to `0`
                for dead_column in dead_columns:
                    row[dead_column] = '0'      

        return self.matrix_initial

    def token_propagation(self, node, value, memoize=False):
        """ Token propagation:
            - propagate reachable/dead places,
            - learn new concurrent/independent places,
            - memoize successors.
        """
        # Initialization
        successors = []

        # Case: partial relation and parents already propagated
        if not self.complete_matrix and all(parent.propagated for parent in node.parents):
            
            # Update `propagated` flag of the node
            node.propagated = True

            # The products of the parents' predecessors are independent
            # Can be treat as change_of_basis
            for parent_1, parent_2 in itertools.combinations(node.parents, 2):
                self.product(parent_1.predecessors, parent_2.predecessors, '0')

            # Set the predecessors of the node
            node.predecessors = [predecessor for parent in node.parents for predecessor in parent.predecessors]

            # Update `dead` flag
            if value == '0':
                # If all parents are dead set the node to dead, otherwise cannot propagate a dead value anymore
                if all(parent == '0' for parent in node.parents):
                    node.dead = True
                else:
                    value = '.'

        # Case: the node is a place from the initial net
        if not node.additional:
            
            # Set its value (if different from '.') in the concurrency matrix (non-dead / dead)
            if value != '.':
                order = self.initial_net.order[node.id]
                self.matrix_initial[order][order] = value
            
            # Add the node to the successors and its predecessors list
            successors.append(node)
            node.predecessors.append(node)

            # Set agglomerated nodes as independent
            for agg_1, agg_2 in itertools.combinations(node.agglomerated, 2):
                agg_1.independent.add(agg_2)
                agg_2.independent.add(agg_1)

        # Token propagation over the agglomerated nodes
        for agglomerated in node.agglomerated:
            agg_successors = self.token_propagation(agglomerated, value)
            successors += agg_successors
            
        # Token propagation over the redundancy nodes
        for redundant in node.redundant:
            red_successors = self.token_propagation(redundant, value)
            # Learn new concurrent places
            if value == '1':
                self.product(red_successors, successors, value)
            successors += red_successors

        # Successors memoization
        if memoize:
            node.successors = successors

        # Return successors
        return successors

    def product(self, places1, places2, value):
        """ Set the cartesian product between two lists of places
            to a value in the initial matrix. 
        """
        for place1, place2 in itertools.product(places1, places2):
            place1 = self.initial_net.order[place1.id]
            place2 = self.initial_net.order[place2.id]
            self.matrix_initial[max(place1, place2)][min(place1, place2)] = value


class Node:
    """
    Node: place or additional variable.

    A node is defined by:
    - an identifier,
    - a Boolean indicating if the node is an additional variable (not in the initial net),
    - a list of redundant nodes,
    - a list of agglomerated nodes,
    - a list of successors in the TFG (optional),
    - a list of predecessors in the TFG (optional).
    """

    def __init__(self, id, additional=False):
        """ Initializer.
        """
        self.id = id
        self.additional = additional
        
        # Incoming arcs (parents)
        self.parents = []

        # Outgoing arcs (children)
        self.redundant = []
        self.agglomerated = []

        # Propagated flag
        self.propagated = False

        # Dead flag
        self.dead = False

        # Succesors and predecessors in the TFG that are not additional
        self.successors = []
        self.predecessors = []

        # Independent nodes set
        self.independent = set()
