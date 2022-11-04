"""
Petri Net Module

Input file format: .pnml
Documentation: http://projects.laas.fr/tina//manuals/formats.html

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

import os.path
import re
import tempfile
import xml.etree.ElementTree as ET
from collections import deque


class PetriNet:
    """
    Petri Net.
    """

    def __init__(self, filename, initial_net=False, no_units=False):
        """ Initializer.
        """
        # List of places
        self.places = []
        self.initial_places = []

        # Places associated to their order 
        self.order = {}

        # Total number of places
        self.number_places = 0

        # Initial net flag
        self.initial_net = initial_net

        # Transitions
        self.pre = {}
        self.post = {}

        # Corresponding NUPN
        self.nupn = None

        # Current file
        self.f_file = None

        # Parse file
        extension = os.path.splitext(filename)[1]
        if extension == '.pnml':
            self.parse_pnml(filename, no_units)
        elif extension == '.net':
            self.parse_net(filename)
        else:
            raise ValueError("Petri net not in .pnml or .net format")

    def __str__(self):
        """ Textual Petri net places.
        """
        return ' '.join(self.places)

    def parse_pnml(self, filename, no_units):
        """ Petri Net parser.
            Input format: .pnml
        """
        xmlns = "{http://www.pnml.org/version-2009/grammar/pnml}"
        ET.register_namespace('', "http://www.pnml.org/version-2009/grammar/pnml")

        tree = ET.parse(filename)
        root = tree.getroot()

        for place_node in root.iter(xmlns + "place"):

            if self.initial_net:
                # If initial net, assume there is no `name/text` element
                place = place_node.attrib['id']

                # Check if there exists one
                text_element = place_node.find(xmlns + "name/" + xmlns + "text")
                if text_element is not None:
                    # If it is the case, set its value to the id
                    text_element.text = place
                else:
                    # If not, create one
                    name = ET.SubElement(place_node, 'name')
                    text = ET.SubElement(name, 'text')
                    text.text = place

            else:
                # If reduced net, take the `name/text` element instead
                place = place_node.find(xmlns + "name/" + xmlns + "text").text

            self.places.append(place)
            self.order[place] = self.number_places
            self.number_places += 1

        if self.initial_net and not no_units:
            # Write the net to a temporary file
            self.f_file = tempfile.NamedTemporaryFile(suffix='.pnml')
            tree.write(self.f_file.name, encoding="utf-8", xml_declaration=True)

            # Check if the net is known to be unit-safe
            structure = root.find(xmlns + "net/" + xmlns + "page/" + xmlns + "toolspecific/" + xmlns + "structure")

            # Exit if no NUPN inforation
            if structure is None:
                return

            # Get unit safe pragma
            unit_safe = structure.attrib["safe"] == "true"
            
            # Create NUPN
            self.nupn = NUPN(unit_safe)

            # Get root unit
            self.nupn.root = self.nupn.get_unit(structure.attrib["root"])

            # Get NUPN information
            for unit in structure.findall(xmlns + 'unit'):
                # Get name
                name = unit.attrib["id"]

                # Get places
                pnml_places = unit.find(xmlns + 'places')
                places = [place for place in pnml_places.text.split()] if pnml_places is not None and pnml_places.text else []

                # Get subunits
                pnml_subunits = unit.find(xmlns + 'subunits')
                subunits = {self.nupn.get_unit(subunit) for subunit in pnml_subunits.text.split()} if pnml_subunits is not None and pnml_subunits.text else set()
                
                # Create new unit
                new_unit = self.nupn.get_unit(name)
                new_unit.places = places
                new_unit.subunits = subunits

            # Set successors
            self.nupn.root.compute_hierarchy()

    def parse_net(self, filename):
        """ Petri Net parser.
            Input format: .net
        """
        try:
            with open(filename, 'r') as fp:
                for line in fp.readlines():

                    content = re.split(r'\s+', line.strip())  

                    # Skip empty lines and get the first identifier
                    if not content:
                        continue
                    else:
                        element = content.pop(0)

                    # Transition arcs
                    if element == "tr":
                        self.parse_transition(content)

                    # Place
                    if element == "pl":
                        self.parse_place(content)
            fp.close()
            self.number_places = len(self.places)
        except FileNotFoundError as e:
            exit(e)

    def parse_transition(self, content):
        """ Transition parser.
            Input format: .net
        """
        transition = content.pop(0).replace('{', '').replace('}', '')

        content = self.parse_label(content)
        arrow = content.index("->")

        self.pre[transition] = [self.parse_arc(arc) for arc in content[0:arrow]]
        self.post[transition] = [self.parse_arc(arc) for arc in content[arrow + 1:]]

    def parse_arc(self, content):
        """ Arc parser.
            Input format: .net
        """
        if '*' in content:
            place = content.split('*')[0].replace('{', '').replace('}', '')
        else:
            place = content.replace('{', '').replace('}', '')

        if place not in self.places:
                self.places.append(place)

        return place

    def parse_place(self, content):
        """ Place parser.
            Input format: .net
        """
        place = content[0].replace('{', '').replace('}', '')

        if place not in self.places:
            self.places.append(place)

        if len(content) > 1 and content[1] == "(1)":
            self.initial_places.append(place)

    def parse_label(self, content):
        """ Label parser.
            Input format: .net
        """
        index = 0
        if content and content[index] == ':':
            label_skipped = content[index + 1][0] != '{'
            index = 2
            while not label_skipped:
                label_skipped = content[index][-1] == '}'
                index += 1
        return content[index:]

    def export_nupn(self, filename):
        """ Export NUPN.
            Format: .nupn
        """
        with open(filename, 'w') as fp:
            fp.write("!creator kong {}\n".format(__version__))

            if self.nupn:
                # Simplify the projected NUPN and update place order
                self.order = self.nupn.simplification()

                # Order places
                self.places.sort(key=lambda pl: self.order[pl])
                
                if self.nupn.unit_safe:
                    fp.write("!unit_safe unknown/tool\n")

            else:
                self.order = {pl: index for index, pl in enumerate(self.places)}

            fp.write("places #{} 0...{}\n".format(self.number_places, self.number_places - 1))
            fp.write("initial places #{}{}\n".format(len(self.initial_places), ' ' + ' '.join(map(lambda pl: str(self.order[pl]), self.initial_places)) if self.initial_places else ""))

            if self.nupn:
                fp.write("units #{} {}...{}\n".format(len(self.nupn.units), 0, len(self.nupn.units) - 1))
                fp.write("root unit 0\n")

                for unit in self.nupn.units.values():

                    number_places = len(unit.places)
                    start, end = (self.order[unit.places[0]], self.order[unit.places[-1]]) if number_places else (1, 0)
            
                    subunits = ' ' + ' '.join(map(lambda subunit: str(self.nupn.order[subunit.id]), unit.subunits)) if unit.subunits else ""

                    fp.write("U{} #{} {}...{} #{}{}\n".format(self.nupn.order[unit.id], number_places, start, end, len(unit.subunits), subunits))

            else:
                fp.write("units #{} 0...{}\n".format(self.number_places + 1, self.number_places))
                fp.write("root unit 0\n")
                fp.write("U0 #0 1...0 #{} {}\n".format(self.number_places, ' '.join([str(i) for i in range(1, self.number_places + 1)])))
                for place in self.places:
                    place_order = self.order[place]
                    fp.write("U{} #1 {}...{} #0\n".format(place_order + 1, place_order, place_order))

            start, end = (0, len(self.pre) - 1) if len(self.pre) else (1, 0)
            fp.write("transitions #{} {}...{}\n".format(len(self.pre), start, end))

            for index, transition in enumerate(self.pre.keys()):
                pre = ' ' + ' '.join(map(lambda pl: str(self.order[pl]), self.pre[transition])) if self.pre[transition] else ""
                post = ' ' + ' '.join(map(lambda pl: str(self.order[pl]), self.post[transition])) if self.post[transition] else ""
                fp.write("T{} #{}{} #{}{}\n".format(index, len(self.pre[transition]), pre, len(self.post[transition]), post))

class NUPN:
    """ NUPN.
    """

    def __init__(self, unit_safe):
        """ Initializer.
        """
        # Unit-safe pragma
        self.unit_safe = unit_safe

        # Root
        self.root = None

        # Unit ids associated to the corresponding unit object
        self.units = {}

        # Order
        self.order = {}

    def __str__(self):
        """ NUPN to textual format.
        """
        # Description
        text = "# NUPN\n"
        text += "# Unit-safe: {}\n".format(self.unit_safe)
        text += "# Root: {}\n".format(self.root.id)

        # Subunits
        text += '\n'.join(map(str, self.units.values()))

        return text

    def get_unit(self, unit):
        """ Return the corresponding unit,
            or create one if does not exist.
        """
        if unit in self.units:
            return self.units[unit]

        new_unit = Unit(unit)
        self.units[unit] = new_unit

        return new_unit

    def add_place(self, place, units):
        """ Add place into the optimal unit among a set of units.
        """
        if len(units) == 1:
            units.pop().places.append(place)
            return

        optimal_unit = min(units, key=lambda unit: sum([len(disjoint_unit.places) for disjoint_unit in set(self.units.values()) - unit.descendants]))
        optimal_unit.places.append(place)

    def simplification(self):
        """ Simplify the units.
            - Merge units that contains only one subunit.
            - Delete units that does not contain any place.
        """
        queue = deque([self.root])

        while queue:

            unit, flag = queue.popleft(), False

            # Current unit contains only one subunit
            if len(unit.subunits) == 1:
                subunit = unit.subunits.pop()
                del self.units[subunit.id]
                unit.places += subunit.places
                unit.subunits = subunit.subunits
                flag = True

            # A subunit does not contain any place
            for subunit in unit.subunits.copy():
                if not subunit.places:
                    del self.units[subunit.id]
                    unit.subunits |= subunit.subunits
                    unit.subunits.remove(subunit)
                    flag = True

            # Add next units to the queue
            if flag:
                queue.append(unit)
            else:
                queue.extend(unit.subunits)

        places_order = {}
        places_counter = 0

        for unit_index, unit in enumerate(self.units.values()):
            self.order[unit.id] = unit_index
            for place in unit.places:
                places_order[place] = places_counter
                places_counter += 1

        return places_order

class Unit:
    """ NUPN Unit.
    """
    
    def __init__(self, id):
        """ Initializer.
        """
        # Id
        self.id = id

        # Set of places
        self.places = []
        
        # Set of subunits
        self.subunits = set()

        # Set of descendant units
        self.descendants = set()

    def __str__(self):
        """ Unit to textual format.
        """
        return "# {}: [{}] - [{}]".format(self.id, ' '.join(self.places), ' '.join(map(lambda subunit: subunit.id, self.subunits)))

    def initialize_places(self):
        """ Remove all the places recursively.
        """
        self.places = []

        for subunit in self.subunits:
            subunit.initialize_places()

    def compute_hierarchy(self):
        """ Compute the descendants recursively.
        """
        descendants = set()
        
        for subunit in self.subunits:
            descendants.union(subunit.compute_hierarchy())

        descendants.add(self)
        return descendants

    def minimal_units(self, leaves, units):
        """ Compute the optimal set of units for
            a given set of leaves (places of the initial net).
        """
        if set(self.places) & leaves:
            units.add(self)
            return

        for subunit in self.subunits:
            subunit.minimal_units(leaves, units)
