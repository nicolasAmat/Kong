#!/bin/bash

# Script to run reductions on a given list of instances.
#
# Usage:
# ./run_reductions.sh INPUTS/ list

shopt -s globstar

MAX=8

# Set paths
PATH_INPUTS=$1
PATH_OUTPUTS="OUTPUTS"

# Create ouputs directory if does not exist
mkdir -p $PATH_OUTPUTS

# Get list of instances
LIST=$2

# Create temporary files
TEMP_FILE_RUN=$(mktemp)


while IFS= read INSTANCE; do

  echo $INSTANCE

  PATH_INSTANCE="${PATH_INPUTS}/${INSTANCE}/model.pnml"
  PATH_OUTPUT="${PATH_OUTPUTS}/${INSTANCE}.out"

  echo "./reducer.py ${PATH_INSTANCE} &> ${PATH_OUTPUT}" >> $TEMP_FILE_RUN

done <$LIST

# Run computations in parallel
cat $TEMP_FILE_RUN | xargs -d'\n' -t -L 1 -I CMD -P $MAX bash -c CMD

# Remove temporary files
rm $TEMP_FILE_RUN

# Exit
echo DONE
exit 0
