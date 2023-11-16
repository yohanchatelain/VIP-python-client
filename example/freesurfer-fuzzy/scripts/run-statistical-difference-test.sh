#!/bin/bash

ROOT=$(realpath $(dirname "${BASH_SOURCE[0]}"))

SCRIPT=${ROOT}/test_statistical_difference.py
DIRECTORY=${ROOT}/../csv

for stat in sig std; do
    for filename in $(ls ${DIRECTORY}/group*${stat}.csv); do
        echo "Parse" $filename
        output=$(echo $(basename $filename) | cut -d'.' -f1)
        echo $output
        python3 ${SCRIPT} --filename ${filename} --output qqplot-${output}
    done
done

mkdir -p figures/qqplot/{html,png}

mv qqplot-group*html figures/qqplot/html
mv qqplot-group*png figures/qqplot/png
