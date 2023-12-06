#!/bin/bash

ROOT=$(realpath $(dirname "${BASH_SOURCE[0]}"))

export SCRIPT=${ROOT}/plot_stats.py
export DIRECTORY=${ROOT}/../csv

function basename_wo_ext() {
    echo $(basename $1) | cut -d'.' -f1
}

function plot() {
    filename=$1
    title=$2
    region=$3
    measure=$4
    ext=$5
    log=$6
    output=$(basename_wo_ext $filename)${ext}
    echo "Parse" $filename
    echo python3 ${SCRIPT} --mca-filename ${filename} --output ${output} \
    --analysis-level ${level} --region="cortical" --measure="${measure}" \
    --xaxis "'${xaxis}'" --yaxis "'${yaxis}'" \
    --title "'${title}'" "${log}" >>$filename.log
    python3 ${SCRIPT} --mca-filename ${filename} --output ${output} \
    --analysis-level ${level} --region="cortical" --measure="${measure}" \
    --xaxis "${xaxis}" --yaxis "${yaxis}" \
    --title "${title}" "${log}" 2>>$filename.log 
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

plot_significant_digits() {
    # Significant digits
    local level=$1
    local measure=$2
    local xaxis="ROI"
    local yaxis="Significant digits"
    local filename="${DIRECTORY}/${level}-${measure}-sig.csv"
    local title=$(get_title "$measure")
    local region=$(get_region "$measure")
    plot "$filename" "$title" "$region" "$measure"
}

plot_standard_deviation() {
    # Standard deviation
    local level=$1
    local measure=$2
    local xaxis="ROI"
    local yaxis="Standard deviation"
    local filename="${DIRECTORY}/${level}-${measure}-std.csv"
    local title=$(get_title "$measure")
    local region=$(get_region "$measure")
    plot "$filename" "$title" "$region" "$measure"
}

plot_standard_deviation_log() {
    # Standard deviation log
    local level=$1
    local measure=$2
    local xaxis="ROI"
    local yaxis="Standard deviation (log)"
    local filename="${DIRECTORY}/${level}-${measure}-std.csv"
    local title=$(get_title "$measure")
    local region=$(get_region "$measure")
    plot "$filename" "$title" "$region" "$measure" "-log" "--log-yaxis"
}

plot_mean() {
    # Mean
    local level=$1
    local measure=$2
    local xaxis="ROI"
    local yaxis="Mean"
    local filename="${DIRECTORY}/${level}-${measure}-mean.csv"
    local title=$(get_title "$measure")
    local region=$(get_region "$measure")
    plot "$filename" "$title" "$region" "$measure"
}

export -f get_title get_region basename_wo_ext plot
export -f plot_significant_digits plot_standard_deviation plot_standard_deviation_log plot_mean

parallel -k --header : plot_significant_digits {level} {measure} ::: level subject group ::: measure area thickness volume subcortical-volume
parallel -k --header : plot_standard_deviation {level} {measure} ::: level subject group ::: measure area thickness volume subcortical-volume
parallel -k --header : plot_standard_deviation_log {level} {measure} ::: level subject group ::: measure area thickness volume subcortical-volume
parallel -k --header : plot_mean {level} {measure} ::: level subject group ::: measure area thickness volume subcortical-volume

cat log

mkdir -p figures/{group,subject}/{png,html}
mv subject-*.png figures/subject/png
mv group-*.png figures/group/png
mv subject-*.html figures/subject/html
mv group-*.html figures/group/html
