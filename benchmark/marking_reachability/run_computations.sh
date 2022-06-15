#!/bin/bash

# Script to run Kong reach and Sift on a given list of instances.
#
# Usage:
# ./run_computations.sh INPUTS/ list

# Set timeout
TIMEOUT=300

# Set max instances
MAX=4

# Set paths
PATH_INPUTS=$1
PATH_OUTPUTS="OUTPUTS/"

# Create ouputs directory if does not exist
mkdir -p $PATH_OUTPUTS

# Get list of instances
LIST=$2

# Create temporary files
TEMP_FILE_RUN=$(mktemp)

# Read instances
while IFS= read INSTANCE; do

  # Display instance name
  echo $INSTANCE

  for INDEX in {0,1,2,3}; do

    # Get relative paths
    PATH_INSTANCE="${PATH_INPUTS}${INSTANCE}/model.pnml"

    PATH_MARKING="${PATH_INPUTS}${INSTANCE}/marking_${INDEX}"
    PATH_FORMULA="${PATH_INPUTS}${INSTANCE}/formula_${INDEX}"

    PATH_OUTPUT_KONG="${PATH_OUTPUTS}${INSTANCE}-${INDEX}_kong.out"
    PATH_OUTPUT_SIFT="${PATH_OUTPUTS}${INSTANCE}-${INDEX}_sift.out"
    
    # Run Kong
    echo "timeout --kill-after=0 ${TIMEOUT} time ../../kong/kong.py reach --show-reduction-ratio ${PATH_INSTANCE} --marking ${PATH_MARKING} &> ${PATH_OUTPUT_KONG}" >> $TEMP_FILE_RUN

    # Run Sift
    echo "timeout --kill-after=0 ${TIMEOUT} time sift ${PATH_INSTANCE} -ff ${PATH_FORMULA} &> ${PATH_OUTPUT_SIFT}" >> $TEMP_FILE_RUN
  done
done <$LIST

# Run computations in parallel
cat $TEMP_FILE_RUN | xargs -d'\n' -t -L 1 -I CMD -P $MAX bash -c CMD

# Remove temporary files
rm $TEMP_FILE_RUN

# Exit
echo DONE
exit 0
