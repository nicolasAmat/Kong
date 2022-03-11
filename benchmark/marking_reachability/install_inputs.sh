#!/bin/bash

# Script to install INPUTS from MCC'2021.


# Delete old files and directories
rm -rv INPUTS/ 2> /dev/null

# Get 2021 MCC models
mkdir INPUTS
wget --no-check-certificate --progress=dot:mega http://mcc.lip6.fr/2021/archives/mcc2021-input.vmdk.tar.bz2
tar -xvjf mcc2021-input.vmdk.tar.bz2
../bin/7z e mcc2021-input.vmdk
../bin/ext2rd 0.img ./:INPUTS
rm -f *.vmdk 0.img *.bz2 1

# Extract archives and remove useless files
cd INPUTS/
rm -rv lost+found
ls *.tgz | xargs -n1 tar -xzvf
rm -v *.tgz

# Exit
echo DONE
exit 0
