#!/bin/bash

# Script to reduce a given list of instances.


# Set paths
PATH_INPUTS="models/mcc.lip6.fr/archives/"
PATH_OUTPUTS="OUTPUTS/reductions/"

# Create ouputs directory if does not exist
mkdir -p $PATH_OUTPUTS

# Get list of instances
LIST=$1

# Read instances
while IFS= read INSTANCE; do

    # Check if there is a 'model.net'
    if [[ -f ${PATH_INPUTS}${INSTANCE} ]]; then
        
        # Get instance name
        INSTANCE_NAME="$(basename -- $INSTANCE .pnml)"

        # Display instance name
        echo $INSTANCE_NAME

        # Run smpt and redirect the result in 'reduction.out'
        ../kong.py --time --reduction-ratio "${PATH_INPUTS}${INSTANCE}" > "${PATH_OUTPUTS}/${INSTANCE_NAME}.out"
    fi

done <$LIST

# Exit
echo DONE
exit 0
