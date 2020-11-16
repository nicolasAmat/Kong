#!/usr/bin/env python3

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
__version__ = "1.0.0"

import sys
import xml.etree.ElementTree as ET


class PetriNet:
    """
    Petri Net places.
    """

    def __init__(self, filename):
        """ Initializer.
        """
        self.places = []
        self.order = {}
        self.number_places = 0

        self.parse_net(filename)

    def __str__(self):
        """ Petri Net places to .net format.
        """
        return ' '.join(self.places) 

    def parse_net(self, filename):
        """ Petri Net parser.
            Input format: .pnml
        """
        xmlns = "{http://www.pnml.org/version-2009/grammar/pnml}"

        tree = ET.parse(filename)
        root = tree.getroot()

        for place_node in root.iter(xmlns + "place"):
            place = place_node.find(xmlns + "name/" + xmlns + "text").text
            self.places.append(place)
            self.order[place] = self.number_places
            self.number_places += 1


if __name__ == "__main__":

    if len(sys.argv) == 1:
        exit("File missing: ./pt.py <path_to_file>")

    net = PetriNet(sys.argv[1])
    print(net.number_places)
