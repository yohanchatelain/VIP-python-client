#!/bin/bash

function get_livingpark_input() {
    local metric="$1"
    if [[ "$metric" == "subcortical_volume" ]]; then
        echo "navr_subcortical_volume.csv"
    else
        echo "navr_cortical_${metric}.csv"
    fi
}

# Plot ENIGMA results for all disorders and metrics
disorders=("22q" "adhd" "asd" "bipolar" "depression" "epilepsy" "ocd" "schizophrenia")
metrics=("thickness" "area" "subcortical_volume")

for disorder in "${disorders[@]}"; do
    for metric in "${metrics[@]}"; do
        echo "Processing disorder: $disorder, metric: $metric"
        LIVINGPARK_INPUT=$(get_livingpark_input "$metric")
        ./container/ENIGMA/threshold_cohen_d.sh \
        --disorder "$disorder" \
        --metric "$metric" \
        --livingpark_input "$PWD/cohen_d/csv/${LIVINGPARK_INPUT}" \
        --output_dir "$PWD/cohen_d_map/enigma"
        echo -e "\n"
    done
done

# Plot Cohen's d for Hettwer et al. 2022
INPUT_DIR="$PWD/container/ENIGMA/data/Hettwer_2022"
disorders=("adhd" "asd" "bd" "mdd" "ocd" "scz")
metrics=("thickness")
for disorder in "${disorders[@]}"; do
    for metric in "${metrics[@]}"; do
        echo "Processing disorder: $disorder, metric: $metric"
        LIVINGPARK_INPUT=$(get_livingpark_input "$metric")
        DISORDER_FILENAME="${INPUT_DIR}/${disorder}_cohen_d.csv"
        ./container/ENIGMA/threshold_cohen_d.sh \
        --disorder "$disorder" \
        --metric "$metric" \
        --disorder_filename "$DISORDER_FILENAME" \
        --livingpark_input "$PWD/cohen_d/csv/${LIVINGPARK_INPUT}" \
        --cohen_d_name "Cohen_d" \
        --vmin "-0.35" \
        --vmax "0.35" \
        --output_dir "$PWD/cohen_d_map/Hettwer_2022"
        echo -e "\n"
    done
done
