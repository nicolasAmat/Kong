#!/bin/bash

# Script to run Kong and caesar.bdd on a given list of instances.


# Set timeout
TIMEOUT=3600
# Set max instances
MAX=8
# Set paths
PATH_INPUTS="models/mcc.lip6.fr/archives/"
PATH_OUTPUTS="OUTPUTS/computations/"

# Check if PNML2NUPN environment variable is defined
if [[ -z ${PNML2NUPN} ]]; then
  echo "PNML2NUPN environment variable is undefined"
  exit 1
fi

# Create ouputs directory if does not exist
mkdir -p $PATH_OUTPUTS

# Get list of instances
LIST=$1

# Create a temporary file
TEMP_FILE=$(mktemp)

# Read instances
while IFS= read INSTANCE; do

    # Get instance name
    INSTANCE_NAME="$(basename -- $INSTANCE .pnml)"

    # Display instance name
    echo $INSTANCE_NAME

    # Get relative path
    PATH_INSTANCE="${PATH_INPUTS}${INSTANCE}"
    PATH_INSTANCE_REDUCED="${PATH_INSTANCE%.*}_reduced.net"
    PATH_INSTANCE_NUPN="${PATH_INSTANCE%.*}.nupn"
    PATH_OUT_KONG="${PATH_OUTPUTS}${INSTANCE_NAME}_Kong.out"
    PATH_OUT_CAESAR="${PATH_OUTPUTS}${INSTANCE_NAME}_caesar.out"

    # Run kong
    echo "timeout ${TIMEOUT} ../kong.py --time ${PATH_INSTANCE} -r ${PATH_INSTANCE_REDUCED} > ${PATH_OUT_KONG}" >> $TEMP_FILE

    # Run PNML2NUPN
    echo "java -jar ${PNML2NUPN} ${PATH_INSTANCE} &> /dev/null" >> $TEMP_FILE

    # Run caesar
    echo "time (timeout ${TIMEOUT} caesar.bdd -concurrent-places ${PATH_INSTANCE_NUPN}) &> ${PATH_OUT_CAESAR}" >> $TEMP_FILE

done <$LIST

# Run previous commands in parallel
cat $TEMP_FILE | xargs -t -L 1 -I CMD -P $MAX bash -c CMD

# Remove the temporary file
rm $TEMP_FILE

# Exit
echo DONE
exit 0
