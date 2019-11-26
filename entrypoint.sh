#!/usr/bin/env bash

# Get parameters
FILENAME=${1}
PINGDOM_API_KEY=${4}

# Make sure a filename was specified
if [[ -z "${FILENAME}" ]]; then
    echo "ERROR: No configuration filename was specified"
    exit 1;
fi

if [[ ! -f "${FILENAME}" ]]; then
    echo "ERROR: The configuration filename specified (${FILENAME}) could not be located"
    exit 2;
fi

# Install Python dependencies
pip install ./requirements.txt

# Execute script
CONFIG_FILENAME=$(echo "${GITHUB_WORKSPACE}/${FILENAME}" | tr -s /)
echo "Loading Configuration File: $C{CONFIG_FILENAME}"
python ./pingdom.py "${CONFIG_FILENAME}" "${PINGDOM_API_KEY}"