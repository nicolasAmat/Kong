#!/usr/bin/env python3

"""
Marking generator script
"""

import argparse
import subprocess
import xml.etree.ElementTree as ET
import multiprocessing


def parse_places(filename):
    """ Get places from .pnml model.
    """
    places = []

    xmlns = "{http://www.pnml.org/version-2009/grammar/pnml}"
    ET.register_namespace('', "http://www.pnml.org/version-2009/grammar/pnml")

    tree = ET.parse(filename)
    root = tree.getroot()

    for place_node in root.iter(xmlns + "place"):
        place = place_node.find(xmlns + "name/" + xmlns + "text").text
        places.append(place)

    return places


def wrapped_walk(args):
    """ Walk wrapper.
    """
    walk(*args)


def walk(inputs, instance):
    """ Find four marking by walking in the net.
    """
    print(instance)

    # Read Petri net places
    path = "{}/{}/model.pnml".format(inputs, instance)
    places = parse_places(path)
    
    # Iter over depths
    for index, depth in enumerate(['1000', '10000', '100000', '1000000']):

        # Get marking
        data = subprocess.run(['walk', path, '-loop', '-c', depth], stdout=subprocess.PIPE).stdout.decode('utf-8')
        marking = data.split('\n')[2].split(": ")[1].split()

        # Write marking (for King)
        with open("{}/{}/marking_{}".format(inputs, instance, index), 'w') as fp:
            fp.write(' '.join(marking))

        # Write formula (for Sift)
        with open("{}/{}/formula_{}".format(inputs, instance, index), 'w') as fp:
            full_marking = {}
            for pl in marking:
                if '*' in pl:
                    pl, tokens = pl.split('*')
                else:
                    tokens = 1
                full_marking[pl] = tokens
            for pl in places:
                if pl not in full_marking:
                    full_marking[pl] = 0
            fp.write('- (' + ' /\ '.join(["{} = {}".format(pl, tokens) for pl, tokens in full_marking.items()]) + ')')


def main():
    """ Main function.
    """
    # Arguments parser
    parser = argparse.ArgumentParser(description='Marking Generator')

    parser.add_argument('inputs',
                        metavar='inputs',
                        type=str,
                        help='path to the INPUTS/ directory')

    parser.add_argument('list',
                        metavar='list',
                        type=str,
                        help='path to the list of instances')

    parser.add_argument('cpu',
                        metavar='cpu',
                        type=int,
                        help='number of CPUs')

    results = parser.parse_args()

    # Read list of instances
    with open(results.list) as fp:
        instance_list = fp.read().split()

    # Iter of instances
    pool = multiprocessing.Pool(results.cpu)
    pool.map(wrapped_walk, [(results.inputs, instance) for instance in instance_list])


if __name__=='__main__':
    main()
    print("DONE")
