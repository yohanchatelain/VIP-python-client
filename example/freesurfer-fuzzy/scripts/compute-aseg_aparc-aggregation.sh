#!/bin/bash

# Check if two arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <subjects_dir> <output_dir>"
    exit 1
fi

ROOT=$(realpath $(dirname "${BASH_SOURCE[0]}"))

# define aparcstats2table and asegstats2table
aparcstats2table=python3 -$(realpath $ROOT/freesurfer/aparcstats2table)
asegstats2table=python3 $(realpath $ROOT/freesurfer/asegstats2table)

# Define the subjects directory and output directory for the tsv files
SUBJECTS_DIR="$1"
OUTPUT_DIR="$2"

# You might want to create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Initialize an array with the different measurement types
MEASUREMENTS=(area volume thickness thicknessstd meancurv)
# Initialize an array with the different hemispheres
HEMIS=(lh rh)

# Initialize an empty array to hold the list of subjects
SUBJECTS=()

# Loop through the subject directories and add them to the SUBJECTS array
for subject_path in "$SUBJECTS_DIR"/sub-*; do
    if [ -d "$subject_path" ]; then # Make sure it's a directory
        subject_name=$(basename "$subject_path")
        SUBJECTS+=("$subject_name")
    fi
done

for rep in rep*/; do
    # Iterate over each measurement type
    for meas in "${MEASUREMENTS[@]}"; do
        # Handle subcortical volume separately as it does not require hemispheric specification
        if [ "$meas" == "volume" ]; then
            asegstats2table --subjects ${SUBJECTS[@]} --meas "$meas" --tablefile "$OUTPUT_DIR/${rep}.aseg.$meas.tsv"
            echo "aseg $meas table created at $OUTPUT_DIR/aseg.$meas.tsv"
        else
            # Loop through hemispheres for cortical measurements
            for hemi in lh rh; do
                aparcstats2table --hemi "$hemi" --subjects ${SUBJECTS[@]} --meas "$meas" --tablefile "$OUTPUT_DIR/${rep}.${hemi}.aparc.$meas.tsv"
                echo "${hemi} hemisphere aparc $meas table created at $OUTPUT_DIR/${hemi}.aparc.$meas.tsv"
            done
        fi
    done
done

echo "TSV files created in $OUTPUT_DIR"
