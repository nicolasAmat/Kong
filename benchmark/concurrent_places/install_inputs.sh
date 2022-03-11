#!/bin/bash

# Script to install models/ from the MCC'2020.


# Delete old files and directories
rm -rv models/ 2> /dev/null

# Get 2020 MCC models
wget --no-check-certificate --progress=dot:mega https://homepages.laas.fr/namat/media/models.tar.gz
tar -xvf models.tar.gz
rm -v models.tar.gz

# Exit
echo DONE
exit 0
