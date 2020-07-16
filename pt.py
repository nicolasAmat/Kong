#!/usr/bin/env python3

"""
Petri Net Module

Input file format: .net
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
import re


class PetriNet:
    """
    Petri Net places.
    """

    def __init__(self, filename):
        """ Initializer.
        """
        self.places = set()
        self.ordered_places = []

        self.parse_net(filename)
        self.order_places()

    def __str__(self):
        """ Petri Net places to .net format.
        """
        return ' '.join(self.ordered_places) 

    def parse_net(self, filename):
        """ Petri Net parser.
            Input format: .net
        """
        try:
            with open(filename, 'r') as fp:
                for line in fp.readlines():
                    content = re.split(r'\s+', line.strip())
                    element = content.pop(0)
                    if element == "tr":
                        self.parse_transition(content)
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
        for pl in content:
            if pl != '->':
                self.places.add(pl.replace('{', '').replace('}', ''))

    def parse_place(self, content):
        """ Place parser.
            Input format: .net
        """
        self.places.add(content.pop(0).replace('{', '').replace('}', ''))

    def parse_label(self, content):
        """ Label parser.
            Input format: .net
        """
        index = 0
        if content[index] == ':':
            label_skipped = content[index + 1][0] != '{'
            index = 2
            while not label_skipped:
                label_skipped = content[index][-1] == '}'
                index += 1
        return content[index:]

    def order_places(self):
        """ Order the places according to an alphanumeric order.
        """
        self.ordered_places = sorted(self.places)


if __name__ == "__main__":

    if len(sys.argv) == 1:
        exit("File missing: ./pt.py <path_to_file>")

    net = PetriNet(sys.argv[1])

    print("Petri Net")
    print("---------")
    print(net)
