#!/bin/bash

ROOT=$(realpath $(dirname "${BASH_SOURCE[0]}"))

SCRIPT=${ROOT}/test_statistical_difference.py
DIRECTORY=${ROOT}/csv

for stat in sig std; do
    for filename in $(ls ${DIRECTORY}/group*${stat}.csv); do
        output=$(basename $(echo $filename | cut -d'.' -f1))
        python3 ${SCRIPT} --filename ${filename} --output qqplot-${output}
    done
done
