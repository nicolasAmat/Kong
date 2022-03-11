#!/bin/bash

# Script to run reductions on a given list of instances.


shopt -s globstar

MAX=8

# Set paths
PATH_INPUTS="../models/mcc.lip6.fr/archives/"
PATH_OUTPUTS="OUTPUTS/"

# Create ouputs directory if does not exist
mkdir -p $PATH_OUTPUTS

# Create temporary files
TEMP_FILE_RUN=$(mktemp)

for INSTANCE in ${PATH_INPUTS}**/PT/*.pnml; do

  FILENAME="$(basename -- $INSTANCE)"
  echo $FILENAME

  PATH_OUT=$PATH_OUTPUTS"${FILENAME%.*}".out
  
  echo "reducer.py ${INSTANCE} &> ${PATH_OUT}" >> $TEMP_FILE_RUN
done

# Run computations in parallel
cat $TEMP_FILE_RUN | xargs -d'\n' -t -L 1 -I CMD -P $MAX bash -c CMD

# Remove temporary files
rm $TEMP_FILE_RUN

# Exit
echo DONE
exit 0
