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

    def __init__(self, filename, initial_net=False):
        """ Initializer.
        """
        # List of places
        self.places = []

        # Places associated to their order 
        self.order = {}

        # Total number of places
        self.number_places = 0

        # Initial net flag
        self.initial_net = initial_net

        # Corresponding NUPN
        self.NUPN = None

        # Current filename
        self.filename = filename

        # Parse file
        extension = os.path.splitext(filename)[1]
        if extension == '.pnml':
            self.parse_pnml(filename)
        elif extension == '.net':
            self.parse_net(filename)
        else:
            raise ValueError("Petri net not in .pnml or .net format")

    def __str__(self):
        """ Textual Petri net places.
        """
        return ' '.join(self.places)

    def parse_pnml(self, filename):
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

        if self.initial_net:
            # Write the net to a temporary file
            self.filename = tempfile.NamedTemporaryFile(suffix='.pnml').name
            tree.write(self.filename, encoding="utf-8", xml_declaration=True)

            # Check if the net is known to be unit-safe
            structure = root.find(xmlns + "net/" + xmlns + "page/" + xmlns + "toolspecific/" + xmlns + "structure")

            # Exit if no NUPN inforation
            if structure is None:
                return

            # Get unit safe pragma
            unit_safe = structure.attrib["safe"] == "true"
            
            # Create NUPN
            self.NUPN = NUPN(unit_safe)

            # Get root unit
            self.NUPN.root = self.NUPN.get_unit(structure.attrib["root"])

            # Get NUPN information
            for unit in structure.findall(xmlns + 'unit'):
                # Get name
                name = unit.attrib["id"]

                # Get places
                pnml_places = unit.find(xmlns + 'places')
                places = {place for place in pnml_places.text.split()} if pnml_places is not None and pnml_places.text else set()

                # Get subunits
                pnml_subunits = unit.find(xmlns + 'subunits')
                subunits = {self.NUPN.get_unit(subunit) for subunit in pnml_subunits.text.split()} if pnml_subunits is not None and pnml_subunits.text else set()
                
                # Create new unit
                new_unit = self.NUPN.get_unit(name)
                new_unit.places = places
                new_unit.subunits = subunits

            # Set successors
            self.NUPN.root.compute_hierarchy()

    def update_order_from_nupn(self, filename):
        """ Parse the place labels from a given .nupn file
            and update the order of the places.
        """
        try:
            # Read the .nupn file
            with open(filename, 'r') as fp:
                # Find the labeling section
                content = re.search(r'labels(.*)', fp.read(), re.DOTALL)

                if content:
                    # Update the order associated to each place
                    for mapping in re.split('\n+', content.group())[1:len(self.places) + 1]:
                        order, place = mapping.split(' ')
                        order = int(order[1:])
                        self.order[place] = order

            # Sort the list of places
            self.places.sort(key=lambda pl: self.order[pl])
        except FileNotFoundError as e:
            exit(e)

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
        except FileNotFoundError as e:
            exit(e)

    def parse_transition(self, content):
        """ Transition parser.
            Input format: .net
        """
        content = self.parse_label(content[1:])
        content.remove('->')

        for arc in content:
            if '*' in arc:
                place = arc.split('*')[0]
            else:
                place = arc

        if place not in self.places:
            self.places.append(place)

    def parse_place(self, content):
        """ Place parser.
            Input format: .net
        """
        place = content[0]

        if place not in self.places:
            self.places.append(place)

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
            units.pop().places.add(place)
            return

        optimal_unit = min(units, key=lambda unit: sum([len(disjoint_unit.places) for disjoint_unit in set(self.units.values()) - unit.descendants]))
        optimal_unit.places.add(place)

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
                unit.places |= subunit.places
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

    def write_toolspecific_pnml(self, filename):
        """ Write the toolspecific part into a given .pnml file
        """
        xmlns = "{http://www.pnml.org/version-2009/grammar/pnml}"
        ET.register_namespace('', "http://www.pnml.org/version-2009/grammar/pnml")

        # Parse .pnml file
        tree = ET.parse(filename)
        root = tree.getroot()

        # Get page
        page = root.find(xmlns + "net/" + xmlns + "page")

        # Set place ids to the corresponding name/text element
        place_mapping = {}
        for place in root.findall(xmlns + "net/" + xmlns + "page/" + xmlns + "place"):
            text = place.find(xmlns + "name/" + xmlns + "text").text
            place_mapping[place.attrib["id"]] = text
            place.attrib["id"] = place.find(xmlns + "name/" + xmlns + "text").text
        for arc in root.findall(xmlns + "net/" + xmlns + "page/" + xmlns + "arc"):
            if arc.attrib["source"] in place_mapping:
                arc.attrib["source"] = place_mapping[arc.attrib["source"]]
            if arc.attrib["target"] in place_mapping:
                arc.attrib["target"] = place_mapping[arc.attrib["target"]] 

        # Create toolspecific element
        toolspecific = ET.SubElement(page, "toolspecific")
        toolspecific.attrib["tool"] = "nupn"
        toolspecific.attrib["version"] = "1.1"

        # Create size element
        size = ET.SubElement(toolspecific, "size")
        size.attrib["places"] = str(len(root.findall(xmlns + "net/" + xmlns + "page/" + xmlns + "place")))
        size.attrib["transitions"] = str(len(root.findall(xmlns + "net/" + xmlns + "page/" + xmlns + "transition")))
        size.attrib["arcs"] = str(len(root.findall(xmlns + "net/" + xmlns + "page/" + xmlns + "arc")))

        # Create structure element
        structure = ET.SubElement(toolspecific, "structure")
        structure.attrib["units"] = str(len(self.units))
        structure.attrib["root"] = self.root.id
        structure.attrib["safe"] = str(self.unit_safe).lower()

        # Create unit elements
        for u in self.units.values():
            unit = ET.SubElement(structure, "unit")
            unit.attrib["id"] = u.id
            places = ET.SubElement(unit, "places")
            places.text = ' '.join(u.places)
            subunits = ET.SubElement(unit, "subunits")
            subunits.text = ' '.join(map(lambda subunit: subunit.id, u.subunits))

        # Write the final .pnml
        tree.write(filename)


class Unit:
    """ NUPN Unit.
    """
    
    def __init__(self, id):
        """ Initializer.
        """
        # Id
        self.id = id

        # Set of places
        self.places = set()
        
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
        self.places = set()

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
        if self.places & leaves:
            units.add(self)
            return

        for subunit in self.subunits:
            subunit.minimal_units(leaves, units)
