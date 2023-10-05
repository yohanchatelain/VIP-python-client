#!/bin/bash

ROOT=$(realpath $(dirname "${BASH_SOURCE[0]}"))

SCRIPT=${ROOT}/plot_stats.py
DIRECTORY=${ROOT}/csv

function basename_wo_ext() {
    echo $(basename $1) | cut -d'.' -f1
}

# Significant digits
xaxis="ROI"
yaxis="Significant digits"

rm -f log

for level in "subject" "group"; do

    filename=${DIRECTORY}/${level}-area-sig.csv
    output=$(basename_wo_ext $filename)
    title="Surface area"
    echo "Parse" $filename
    python3 ${SCRIPT} --mca-filename ${filename} --output ${output} \
        --analysis-level ${level} \
        --xaxis "${xaxis}" --yaxis "${yaxis}" \
        --title "${title}" 2>>log

    filename=${DIRECTORY}/${level}-thickness-sig.csv
    output=$(basename_wo_ext $filename)
    title="Cortical thickness"
    echo "Parse" $filename
    python3 ${SCRIPT} --mca-filename ${filename} --output ${output} \
        --analysis-level ${level} \
        --xaxis "${xaxis}" --yaxis "${yaxis}" \
        --title "${title}" 2>>log

    filename=${DIRECTORY}/${level}-volume-sig.csv
    output=$(basename_wo_ext $filename)
    title="Cortical volume"
    echo "Parse" $filename
    python3 ${SCRIPT} --mca-filename ${filename} --output ${output} \
        --analysis-level ${level} \
        --xaxis "${xaxis}" --yaxis "${yaxis}" \
        --title "${title}" 2>>log

    filename=${DIRECTORY}/${level}-subcortical-volume-sig.csv
    output=$(basename_wo_ext $filename)
    title="Subcortical volume"
    echo "Parse" $filename
    python3 ${SCRIPT} --mca-filename ${filename} --output ${output} \
        --analysis-level ${level} \
        --xaxis "${xaxis}" --yaxis "${yaxis}" \
        --title "${title}" 2>>log

done

# Standard deviation
xaxis="ROI"
yaxis="Standard deviation (log)"

for level in "subject" "group"; do

    filename=${DIRECTORY}/${level}-area-std.csv
    output=$(basename_wo_ext $filename)
    title="Surface area"
    echo "Parse" $filename
    python3 ${SCRIPT} --mca-filename ${filename} --output ${output} \
        --analysis-level ${level} \
        --xaxis "${xaxis}" --yaxis "${yaxis}" \
        --title "${title}" --log-yaxis 2>>log

    filename=${DIRECTORY}/${level}-thickness-std.csv
    output=$(basename_wo_ext $filename)
    title="Cortical thickness"
    echo "Parse" $filename
    python3 ${SCRIPT} --mca-filename ${filename} --output ${output} \
        --analysis-level ${level} \
        --xaxis "${xaxis}" --yaxis "${yaxis}" \
        --title "${title}" --log-yaxis 2>>log

    filename=${DIRECTORY}/${level}-volume-std.csv
    output=$(basename_wo_ext $filename)
    title="Cortical volume"
    echo "Parse" $filename
    python3 ${SCRIPT} --mca-filename ${filename} --output ${output} \
        --analysis-level ${level} \
        --xaxis "${xaxis}" --yaxis "${yaxis}" \
        --title "${title}" --log-yaxis 2>>log

    filename=${DIRECTORY}/${level}-subcortical-volume-std.csv
    output=$(basename_wo_ext $filename)
    title="Subcortical volume"
    echo "Parse" $filename
    python3 ${SCRIPT} --mca-filename ${filename} --output ${output} \
        --analysis-level ${level} \
        --xaxis "${xaxis}" --yaxis "${yaxis}" \
        --title "${title}" --log-yaxis 2>>log

done

# Mean
xaxis="ROI"
yaxis="Mean"

for level in "subject" "group"; do

    filename=${DIRECTORY}/${level}-area-mean.csv
    output=$(basename_wo_ext $filename)
    title="Surface area"
    echo "Parse" $filename
    python3 ${SCRIPT} --mca-filename ${filename} --output ${output} \
        --analysis-level ${level} \
        --xaxis "${xaxis}" --yaxis "${yaxis}" \
        --title "${title}" 2>>log

    filename=${DIRECTORY}/${level}-thickness-mean.csv
    output=$(basename_wo_ext $filename)
    title="Cortical thickness"
    echo "Parse" $filename
    python3 ${SCRIPT} --mca-filename ${filename} --output ${output} \
        --analysis-level ${level} \
        --xaxis "${xaxis}" --yaxis "${yaxis}" \
        --title "${title}" 2>>log

    filename=${DIRECTORY}/${level}-volume-mean.csv
    output=$(basename_wo_ext $filename)
    title="Cortical volume"
    echo "Parse" $filename
    python3 ${SCRIPT} --mca-filename ${filename} --output ${output} \
        --analysis-level ${level} \
        --xaxis "${xaxis}" --yaxis "${yaxis}" \
        --title "${title}" 2>>log

    filename=${DIRECTORY}/${level}-subcortical-volume-mean.csv
    output=$(basename_wo_ext $filename)
    title="Subcortical volume"
    echo "Parse" $filename
    python3 ${SCRIPT} --mca-filename ${filename} --output ${output} \
        --analysis-level ${level} \
        --xaxis "${xaxis}" --yaxis "${yaxis}" \
        --title "${title}" 2>>log

done

cat log
