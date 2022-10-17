"""
Utils functions to proceed inputs/outputs.

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

import sys

CAESAR_BDD_MAPPER = {
    '1': '1',
    '0': '0',
    '=': '0',
    '<': '0',
    '>': '0',
    '.': '.',
    '~': '.',
    '[': '.',
    ']': '.'
}


def show_matrix(matrix, net, no_rle=False, place_names=False):
    """ Show concurrency matrix.
        (using run-length encoding)
    """
    if not net.places:
        return

    if place_names:
        max_len = max([len(pl) for pl in net.places])

    if net.initial_net:
        prefix = ''
        output_file = sys.stdout
    else:
        prefix = '# '
        output_file = sys.stderr

    if len(matrix) > 0 and not isinstance(matrix[0], list):
        matrix = (matrix,)

    for pl, line in zip(net.places, matrix):
        if place_names:
            text = prefix + pl + ' ' * (max_len - len(pl) + 2)
        else:
            text = prefix

        for i in range(len(line)):
            elem = line[i]
            if no_rle:
                text += elem
            else:
                if i == 0:
                    previous = elem
                    counter = 0
                if i == len(line) - 1:
                    if previous != elem:
                        text += rle_compression(previous, counter)
                        text += elem
                    else:
                        text += rle_compression(previous, counter + 1)
                else:
                    if elem != previous:
                        text += rle_compression(previous, counter)
                        previous = elem
                        counter = 1
                    else:
                        counter += 1

        print(text, file=output_file)


def rle_compression(elem, counter):
    """ Run-length encoding helper.
    """
    if counter < 4:
        return str(elem) * counter
    else:
        return "{}({})".format(elem, counter)


def matrix_from_str(matrix_str):
    """ Return matrix from caesar.bdd output.
        (with run-length encoding)
    """
    matrix_str = matrix_str.split('\n')

    if matrix_str == '':
        return [], False 

    matrix, complete_matrix = [], True

    # Iterate over lines
    for line in matrix_str:

        if not len(line):
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
                value = CAESAR_BDD_MAPPER[value]
                if value == '.':
                    complete_matrix = False
                new_line.append(value)
                past_value = value

        matrix.append(new_line)

    return matrix, complete_matrix


def marking_parser(marking_str):
    """ Parse marking.
    """
    marking = {}

    for place_marking in marking_str.split():
        place_marking = place_marking.split('*')

        if len(place_marking) > 1:
            tokens = int(place_marking[1])
        else:
            tokens = 1

        marking[place_marking[0]] = tokens

    return marking
