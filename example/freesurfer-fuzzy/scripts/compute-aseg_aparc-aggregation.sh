#!/bin/bash

true=0
false=1
MAX_THREADS=32

# Check if two arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <experiments_dir> <output_dir>"
    exit 1
fi

TEMP_DIR=/scratch/ychatel/VIP-python-client/example/freesurfer-fuzzy/vip_outputs/freesurfer-fuzzy/
ROOT=$(realpath $(dirname "${BASH_SOURCE[0]}"))

# define aparcstats2table and asegstats2table
aparcstats2table=$(realpath $ROOT/freesurfer/aparcstats2table)
asegstats2table=$(realpath $ROOT/freesurfer/asegstats2table)

# Define the subjects directory and output directory for the tsv files
EXPERIMENTS_DIR="$1"
OUTPUT_DIR="$2"

# You might want to create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Initialize an array with the different measurement types
MEASUREMENTS=(area volume thickness thicknessstd meancurv)
# Initialize an array with the different hemispheres
HEMIS=(lh rh)

# Function to search for a file
search_file() {
    find "$directory" -type f -name "$1" -print -quit
}

must_extract() {
    tgz_path=$1
    tgz_basename=$(basename $tgz_path)
    subject_name=${tgz_basename%.*}
    directory=$TEMP_DIR/$rep/$subject_name

    # Check if the directory exists
    if [ -d "$directory" ]; then

        # Look for aseg.stats and {l,}h.aparc.a2009s.stats files at any depth within the directory
        aseg_file=$(search_file "aseg.stats")
        lh_file=$(search_file "lh.aparc.a2009s.stats")
        rh_file=$(search_file "rh.aparc.a2009s.stats")

        # Check if both files were found
        if [ -n "$aseg_file" ] && [ -n "$lh_file" ] && [ -n "$rh_file" ]; then
            return $false
        else
            return $true
        fi
    else
        return $true
    fi
}

extract() {
    tar_path=$1
    echo "Extract $tar_path in $TEMP_DIR/$rep"
    mkdir -p $TEMP_DIR/$rep
    tar x -C $TEMP_DIR/$rep -f $rep/$(basename ${tar_path}) --wildcards */aseg.stats */lh.aparc.a2009s.stats */rh.aparc.a2009s.stats
}

get_subjects() {
    # Initialize an empty array to hold the list of subjects
    SUBJECTS=()

    # Loop through the subject directories and add them to the SUBJECTS array
    counter=1
    for subject_path in "$SUBJECTS_DIR"/sub-*; do
        if [[ "$subject_path" == *.tgz ]]; then
            if must_extract $subject_path; then
                extract $subject_path &
                if [ $((counter % MAX_THREADS)) -eq 0 ]; then
                    wait -n
                    counter=$((counter - 1))
                fi
            else
                echo "Skip extraction ${subject_path}"
            fi
            ((counter++))
            subject_name_tgz=$(basename "$subject_path")
            subject_name=${subject_name_tgz%.*}
            SUBJECTS+=("$subject_name")
        fi
    done
}

for rep in rep*/; do
    echo "Parse ${rep}"

    # Get subjects name-
    SUBJECTS_DIR=$EXPERIMENTS_DIR/$rep
    echo "Getting subjects for ${SUBJECTS_DIR}"
    get_subjects

    export SUBJECTS_DIR=$TEMP_DIR/$rep
    # Iterate over each measurement type
    for meas in "${MEASUREMENTS[@]}"; do
        # Handle subcortical volume separately as it does not require hemispheric specification
        if [ "$meas" == "volume" ]; then
            python3 $asegstats2table --skip --subjects ${SUBJECTS[@]} --meas "$meas" --tablefile "$OUTPUT_DIR/${rep}.aseg.$meas.tsv"
            echo "aseg $meas table created at $OUTPUT_DIR/aseg.$meas.tsv"
        else
            # Loop through hemispheres for cortical measurements
            for hemi in lh rh; do
                python3 $aparcstats2table --skip --parc aparc.a2009s --hemi "$hemi" --subjects ${SUBJECTS[@]} --meas "$meas" --tablefile "$OUTPUT_DIR/${rep}.${hemi}.aparc.$meas.tsv"
                echo "${hemi} hemisphere aparc $meas table created at $OUTPUT_DIR/${hemi}.aparc.$meas.tsv"
            done
        fi
    done
done

echo "TSV files created in $OUTPUT_DIR"
