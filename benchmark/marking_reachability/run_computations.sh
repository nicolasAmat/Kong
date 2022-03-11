#!/bin/bash

# Script to run King and sift on a given list of instances.


# Set timeout
TIMEOUT=300
# Set max instances
MAX=4
# Set paths
PATH_INPUTS="INPUTS/"
PATH_OUTPUTS="OUTPUTS/"

# Create ouputs directory if does not exist
mkdir -p $PATH_OUTPUTS

# Get list of instances
LIST=$1

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
    PATH_OUT_KING="${PATH_OUTPUTS}${INSTANCE}-${INDEX}_king.out"
    PATH_OUT_SIFT="${PATH_OUTPUTS}${INSTANCE}-${INDEX}_sift.out"
    
    # Run kong
    echo "timeout --kill-after=0 ${TIMEOUT} time ../../kong/kong.py reach --show-reduction-ratio ${PATH_INSTANCE} --marking ${PATH_MARKING} &> ${PATH_OUT_KING}" >> $TEMP_FILE_RUN

    # Run sift
    echo "timeout --kill-after=0 ${TIMEOUT} time sift ${PATH_INSTANCE} -ff ${PATH_FORMULA} &> ${PATH_OUT_SIFT}" >> $TEMP_FILE_RUN
  done
done <$LIST

# Run computations in parallel
cat $TEMP_FILE_RUN | xargs -d'\n' -t -L 1 -I CMD -P $MAX bash -c CMD

# Remove temporary files
rm $TEMP_FILE_RUN

# Exit
echo DONE
exit 0
