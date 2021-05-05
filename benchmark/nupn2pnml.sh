#!/bin/bash

# Script to convert .nunpn nets in a given directory to .pnml format.

DIR=$1
cd $DIR

for f in *.nupn ; do
    filename="${f%.*}"
    echo $filename
    caesar.bdd -pnml $f > ${filename}.pnml
    ndrio ${filename}.pnml ${filename}.net
    ndrio ${filename}.net ${filename}.pnml 
    rm ${filename}.net
done

echo DONE
exit 0
