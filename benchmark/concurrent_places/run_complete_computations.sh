#!/bin/bash

# Script to run Kong and Caesar.bdd on a given list of instances.
# Compute complete matrices.
#
# Usage:
# ./run_complete_computations.sh INPUTS/ list


# Set timeout
TIMEOUT=900

# Set max instances
MAX=4

# Set paths
PATH_INPUTS=$1
PATH_OUTPUTS="OUTPUTS/complete_computations/"

# Check if PNML2NUPN environment variable is defined
if [[ -z ${PNML2NUPN} ]]; then
  echo "PNML2NUPN environment variable is undefined"
  exit 1
fi

# Create ouputs directory if does not exist
mkdir -p $PATH_OUTPUTS

# Get list of instances
LIST=$2

# Create temporary files
TEMP_FILE_NUPN=$(mktemp)
TEMP_FILE_RUN=$(mktemp)

# Read instances
while IFS= read INSTANCE; do

    # Display instance name
    echo $INSTANCE

    # Get relative path
    PATH_INSTANCE="${PATH_INPUTS}/${INSTANCE}/model.pnml"
    PATH_INSTANCE_NUPN="${PATH_INSTANCE%.*}.nupn"
    
    PATH_OUTPUT_KONG="${PATH_OUTPUTS}/${INSTANCE}_kong.out"
    PATH_OUTPUT_CAESAR="${PATH_OUTPUTS}/${INSTANCE}_caesar.out"

    # Run Kong
    echo "timeout --kill-after=0 ${TIMEOUT} time ../../kong/kong.py conc ${PATH_INSTANCE} --no-units --show-reduction-ratio --time  &> ${PATH_OUTPUT_KONG}" >> $TEMP_FILE_RUN

    # Run PNML2NUPN
    echo "java -jar ${PNML2NUPN} ${PATH_INSTANCE} &> /dev/null" >> $TEMP_FILE_NUPN

    # Run Caesar.bdd
    echo "timeout --kill-after=0 ${TIMEOUT} time caesar.bdd -concurrent-places ${PATH_INSTANCE_NUPN} &> ${PATH_OUTPUT_CAESAR}" >> $TEMP_FILE_RUN

done <$LIST

# Compute trivial NUPNs in parallel
cat $TEMP_FILE_NUPN | xargs -t -L 1 -I CMD -P $MAX bash -c CMD

# Run computations in parallel
cat $TEMP_FILE_RUN | xargs -t -L 1 -I CMD -P $MAX bash -c CMD

# Remove temporary files
rm $TEMP_FILE_NUPN
rm $TEMP_FILE_RUN

# Exit
echo DONE
exit 0
