#!/bin/bash

ROOT=$(realpath $(dirname "${BASH_SOURCE[0]}"))

SCRIPT=${ROOT}/plot_stats.py
DIRECTORY=${ROOT}/../csv

function basename_wo_ext() {
    echo $(basename $1) | cut -d'.' -f1
}

function plot() {
    filename=$1
    title=$2
    region=$3
    output=$(basename_wo_ext $filename)
    echo "Parse" $filename
    python3 ${SCRIPT} --mca-filename ${filename} --output ${output} \
        --analysis-level ${level} --region="cortical" \
        --xaxis "${xaxis}" --yaxis "${yaxis}" \
        --title "${title}" 2>>log &
}

get_title() {
    case "$1" in
    "area") echo "Surface area" ;;
    "thickness") echo "Cortical thickness" ;;
    "volume") echo "Cortical volume" ;;
    "subcortical-volume") echo "Subcortical volume" ;;
    *) echo "Unknown title" ;;
    esac
}

get_region() {
    case "$1" in
    "area") echo "cortical" ;;
    "thickness") echo "cortical" ;;
    "volume") echo "cortical" ;;
    "subcortical-volume") echo "subcortical" ;;
    *) echo "Unknown region" ;;
    esac
}

rm -f log

# Significant digits
xaxis="ROI"
yaxis="Significant digits"
for level in "subject" "group"; do
    for datatype in "area" "thickness" "volume" "subcortical-volume"; do
        filename="${DIRECTORY}/${level}-${datatype}-sig.csv"
        title=$(get_title "$datatype")
        region=$(get_region "$datatype")
        plot "$filename" "$title" "$region"
    done
done

# Standard deviation
xaxis="ROI"
yaxis="Standard deviation (log)"
for level in "subject" "group"; do
    for datatype in "area" "thickness" "volume" "subcortical-volume"; do
        filename="${DIRECTORY}/${level}-${datatype}-std.csv"
        title=$(get_title "$datatype")
        region=$(get_region "$datatype")
        plot "$filename" "$title" "$region"
    done
done

# Mean
xaxis="ROI"
yaxis="Mean"
for level in "subject" "group"; do
    for datatype in "area" "thickness" "volume" "subcortical-volume"; do
        filename="${DIRECTORY}/${level}-${datatype}-mean.csv"
        title=$(get_title "$datatype")
        region=$(get_region "$datatype")
        plot "$filename" "$title" "$region"
    done
done

wait

cat log

mkdir -p figures/{group,subject}/{png,html}
mv subject-*.png figures/subject/png
mv group-*.png figures/group/png
mv subject-*.html figures/subject/html
mv group-*.html figures/group/html
