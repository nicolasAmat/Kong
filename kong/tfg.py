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

try:
    from graphviz import Graph
except ImportError:
    Graph = None


class TFG:
    """
    Token Flow Graph.
    """

    def __init__(self, filename, initial_net, reduced_net, show_equations=False):
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

    def draw_graph(self):
        """ Draw the Token Flow Graph.
        """
        assert Graph is not None, "Could not import the package `graphviz'"

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
            new_node = Node(place)
            self.nodes[place] = new_node

    def get_node(self, id_node):
        """ Return the node that corresponds to the id if it exists,
            otherwise create a new one and return it.
        """
        if id_node.isdigit() and id_node != '0':
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
                            if not '# net' in line:
                                print(line)
                        inequation_flag = '<=' in line
                        self.parse_equation(re.split(r'\s+', line.replace(' |- ', ' ').replace('# ', '').replace(' <= ', ' ').replace(' = ', ' ').replace(' + ', ' ').replace('{', '').replace('}', '')), inequation_flag)

        except FileNotFoundError as e:
            exit(e)

    def parse_equation(self, equation, inequation_flag=False):
        """ Equation parser.
            Input format: .net (output of the `reduced` tool)
        """
        # Split equation
        kind = equation.pop(0)

        # Skip comment on the bound
        if kind == 'net':
            return

        nodes = [self.get_node(id_node) for id_node in equation]

        # Redundance (Constant or Duplication or Shortcut)
        if kind in ['R', 'I']:
            child = nodes.pop(0)
            for parent in nodes:
                parent.redundant.append(child)
                if inequation_flag:
                    parent.interval = True
                child.parents.append(parent)
            return

        # Agglomeration
        if kind == 'A':
            parent = nodes.pop(0)
            for child in nodes:
                parent.agglomerated.append(child)
                child.parents.append(parent)
            return

        raise ValueError("Invalid reduction equation")

    def units_projection(self):
        """ Project the units.
        """
        # Dict associating each place of the reduced net, to the optimal units
        minimal_units = {}

        # Iterate over the places of the reduced net
        for place in self.reduced_net.places:
 
            # Find leaves
            leaves = set()
            self.explore_leaves(self.nodes[place], leaves)

            # Compute optimal units
            units = set()
            self.initial_net.nupn.root.minimal_units(leaves, units)
            minimal_units[place] = units

        # Transfer the NUPN from the initial net to the reduced net
        self.reduced_net.nupn, self.initial_net.nupn = self.initial_net.nupn, None

        # Clean the NUPN
        self.reduced_net.nupn.root.initialize_places()

        # Project units
        for place in sorted(self.reduced_net.places, key=lambda pl: len(minimal_units[pl])):
            self.reduced_net.nupn.add_place(place, minimal_units[place])

    def explore_leaves(self, node, leaves=set()):
        """ Update the set of nodes that are not additional.
        """
        if not node.additional:
            leaves.add(node.id)

        for succ in node.agglomerated + node.redundant:
            self.explore_leaves(succ, leaves)

    def token_propagation(self, node, value, matrix, complete_matrix, memoize=False):
        """ Token propagation:
            - propagate non dead/dead places,
            - learn new concurrent/independent places,
            - memoize successors.
        """
        # Initialization
        successors = []

        # Case: partial relation and parents already propagated
        if not complete_matrix and all(parent.propagated for parent in node.parents):

            # Update `propagated` flag of the node
            node.propagated = True

            # Set redundant nodes as independent
            for red_1, red_2 in itertools.combinations(node.parents, 2):
                red_1.independent.add(red_2)
                red_2.independent.add(red_1)

            # Set the predecessors of the node
            node.predecessors = [predecessor for parent in node.parents for predecessor in parent.predecessors]

        # Case: partial relation
        if not complete_matrix:

            # Update `dead` flag
            if value == '0':
                # If all parents are dead set the node to dead, otherwise cannot propagate a dead value anymore
                if all(parent.dead for parent in node.parents):
                    node.dead = True
                else:
                    value = '.'

        # Case: the node is a place from the initial net
        if not node.additional:
            
            # Set its value (if different from '.') in the concurrency matrix (non-dead / dead)
            if value != '.':
                order = self.initial_net.order[node.id]
                matrix[order][order] = value

            # Add the node to the successors and predecessors lists
            successors.append(node)
            node.predecessors.append(node)

        # Set agglomerated nodes as independent
        for agg_1, agg_2 in itertools.combinations(node.agglomerated, 2):
            agg_1.independent.add(agg_2)
            agg_2.independent.add(agg_1)

        # Token propagation over the agglomerated nodes
        for agglomerated in node.agglomerated:
            agg_successors = self.token_propagation(agglomerated, value, matrix, complete_matrix)
            successors += agg_successors
            
        # Token propagation over the redundancy nodes
        for redundant in node.redundant:
            red_successors = self.token_propagation(redundant, value, matrix, complete_matrix)
            # Learn new concurrent places
            if value == '1':
                self.product(red_successors, successors, value, matrix)
            successors += red_successors

        # Successors memoization
        if memoize:
            node.successors = successors

        # Return successors
        return successors

    def concurrency_matrix(self, reduced_matrix, complete_matrix):
        """ Change of Dimension Algorithm for Concurrency Matrix.
        """
        # Matrix initialization
        if complete_matrix:
            relation = '0'
        else:
            relation = '.'
        matrix = [[relation for _ in range(i + 1)] for i in range(self.initial_net.number_places)]

        # Propagate non-dead roots
        for non_dead_root in self.non_dead_roots:
            self.token_propagation(non_dead_root, '1', matrix, complete_matrix, memoize=True)

        # Case: partial relation
        if not complete_matrix:
            # Propagate dead root
            self.token_propagation(self.dead_root, '0', matrix, complete_matrix, memoize=True)

        # Propagate roots values (from the reduced net)
        for i in range(self.reduced_net.number_places):

            # Get corresponding root and matrix value
            root = self.get_node(self.reduced_net.places[i])
            value = reduced_matrix[i][i]

            # Alive root
            if value == '1':
                self.token_propagation(root, value, matrix, complete_matrix, memoize=True)
                # Product with non-dead roots
                for non_dead_root in self.non_dead_roots:
                    self.product(non_dead_root.successors, root.successors, value, matrix)

            # Case: partial relation and root not already propagated
            if not complete_matrix and value != '1':
                self.token_propagation(root, value, matrix, complete_matrix, memoize=True)

        # Product with non-dead roots
        for non_dead_root_1, non_dead_root_2 in itertools.combinations(self.non_dead_roots, 2):
            self.product(non_dead_root_1.successors, non_dead_root_2.successors, '1', matrix)

        # Propagate the concurrency relation from the reduced matrix
        for i, line in enumerate(reduced_matrix):

            # Skip dead roots
            if line[i] == '0':
                continue
            
            # Only iterate over the lower triangle (symmetric relation)
            for j, concurrency in enumerate(line[:-1]):

                # The product of the concurrent roots' successors is included in the concurrency relation
                if concurrency == '1':
                    root_1, root_2 = self.get_node(self.reduced_net.places[i]), self.get_node(self.reduced_net.places[j])
                    self.product(root_1.successors, root_2.successors, '1', matrix)

                # Case: partial relation
                if not complete_matrix and concurrency == '0':
                    # Set roots as independent
                    root_1, root_2 = self.get_node(self.reduced_net.places[i]), self.get_node(self.reduced_net.places[j])
                    root_1.independent.add(root_2)
                    root_2.independent.add(root_1)

        # Case: partial relation
        if not complete_matrix:

            # Queue initialization
            queue = deque()

            # Add non-dead roots
            for non_dead_root in self.non_dead_roots:
                queue.append(non_dead_root)

            # Add places from reduced net
            for place_id in self.reduced_net.places:
                queue.append(self.get_node(place_id))

            while queue:
                # Get first node in the queue
                node = queue.popleft()

                # Iterate over the intersection of the independent places from the non-dead parents parents
                non_dead_parents = [parent.independent for parent in node.parents if not parent.dead]
                if non_dead_parents:
                    for independent_node in set.intersection(*non_dead_parents): 
                        # Add the independency relation in nodes
                        node.independent.add(independent_node)
                        independent_node.independent.add(node)

                # Add the independency relations in the matrix for places from the initial net
                if not node.additional:
                    self.product([node], [independent_node for independent_node in node.independent if not independent_node.additional], '0', matrix)

                # Add children to the queue
                for child in node.agglomerated + node.redundant:
                    queue.append(child)

        # Case: partial relation
        # Dead places are independent to all others places
        dead_columns = []
        for i, row in enumerate(matrix):
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

        return matrix

    def product(self, places1, places2, value, matrix):
        """ Set the cartesian product between two lists of places
            to a value in the initial matrix. 
        """
        for place1, place2 in itertools.product(places1, places2):
            place1 = self.initial_net.order[place1.id]
            place2 = self.initial_net.order[place2.id]
            matrix[max(place1, place2)][min(place1, place2)] = value

    def lazy_token_propagation(self, node, value, vector, complete_vector):
        """ Lazy token propagation:
            - propagate non dead/dead places.
        """
        # Initialization
        successors = []

        # Case: partial relation and parents already propagated
        if not complete_vector and all(parent.propagated for parent in node.parents):

            # Update `propagated` flag of the node
            node.propagated = True

            # Set the predecessors of the node
            node.predecessors = [predecessor for parent in node.parents for predecessor in parent.predecessors]

        # Case: partial relation
        if not complete_vector:

            # Update `dead` flag
            if value == '1':
                # If all parents are dead set the node to dead, otherwise cannot propagate a dead value anymore
                if all(parent.dead for parent in node.parents):
                    node.dead = True
                else:
                    value = '.'

        # Case: the node is a place from the initial net
        if not node.additional:
            
            # Set its value (if different from '.') in the dead vector (non-dead / dead)
            if value != '.':
                order = self.initial_net.order[node.id]
                vector[order] = value

        # Token propagation over the agglomerated nodes
        for agglomerated in node.agglomerated:
            agg_successors = self.lazy_token_propagation(agglomerated, value, vector, complete_vector)
            successors += agg_successors
            
        # Token propagation over the redundancy nodes
        for redundant in node.redundant:
            red_successors = self.lazy_token_propagation(redundant, value, vector, complete_vector)
            successors += red_successors

        # Return successors
        return successors

    def dead_places_vector(self, reduced_vector, complete_vector):
        """ Change of Dimension Algorithm for Dead Places Vector.
        """
        # Matrix initialization
        if complete_vector:
            relation = '1'
        else:
            relation = '.'
        vector = [relation for i in range(self.initial_net.number_places)]

        # Propagate non-dead roots
        for non_dead_root in self.non_dead_roots:
            self.lazy_token_propagation(non_dead_root, '0', vector, complete_vector)

        # Case: partial relation
        if not complete_vector:
            # Propagate dead root
            self.token_propagation(self.dead_root, '1', vector, complete_vector)

        # Propagate roots values (from the reduced net)
        for i in range(self.reduced_net.number_places):

            # Get corresponding root and matrix value
            root = self.get_node(self.reduced_net.places[i])
            value = reduced_vector[i]

            # Alive root
            if value == '0':
                self.lazy_token_propagation(root, value, vector, complete_vector)

            # Case: partial relation and root not already propagated
            if not complete_vector and value == '1':
                self.lazy_token_propagation(root, value, vector, complete_vector)

        return vector

    def marking_projection(self, initial_marking):
        """ Marking projection algorithm.
        """
        # Initialize configuration
        configuration = {}
        # Set initial marking
        for pl in self.initial_net.places:
            if pl in initial_marking:
                configuration[self.get_node(pl)] = initial_marking[pl]
            else:
                configuration[self.get_node(pl)] = 0
        # Set nondead roots
        for root in self.non_dead_roots:
            configuration[root] = int(root.id.split('#')[0])
        # Set dead root
        configuration[self.dead_root] = 0

        # Bottom-up propagation
        for root in [self.get_node(place) for place in self.reduced_net.places] + [self.dead_root] + self.non_dead_roots:
            if not self.bottom_up_token_propagation(root, configuration):
                return None

        # Restrict configuration to the reduced net
        return {place: configuration[self.get_node(place)] for place in self.reduced_net.places}

    def bottom_up_token_propagation(self, node, configuration):
        """ Bottom up token propagation for marking projection.
        """
        # Bottom-up token propagation
        for succ in node.redundant + node.agglomerated:
            if not self.bottom_up_token_propagation(succ, configuration):
                return False

        # Set agglomeration configuration
        if node.agglomerated:
            configuration[node] = sum([configuration[agg] for agg in node.agglomerated])

        # Set propagated
        node.propagated = True

        # Check well-definedness
        if node.redundant:
            for red in node.redundant:
                if all(parent.propagated for parent in red.parents):
                    if any([parent.interval for parent in red.parents]):
                        if sum([configuration[parent] for parent in red.parents]) < configuration[red]:
                            return False
                    else:
                        if sum([configuration[parent] for parent in red.parents]) != configuration[red]:
                            return False

        return True
        

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
        # Id
        self.id = id

        # Flag indicating if the node is an additional variable
        self.additional = additional

        # Flag indicating if the node is an interval
        self.interval = False

        # Incoming arcs (parents)
        self.parents = []

        # Outgoing arcs (children)
        self.redundant = []
        self.agglomerated = []

        # Propagation flag
        self.propagated = False

        # Dead flag
        self.dead = False

        # Succesors and predecessors in the TFG that are not additional
        self.successors = []
        self.predecessors = []

        # Independent nodes set
        self.independent = set()
